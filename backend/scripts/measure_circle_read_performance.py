"""Measure the Work 2 public Circle reads against an isolated PostgreSQL database."""

import argparse
import asyncio
import json
import math
import time
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid5

import httpx
from sqlalchemy import delete, insert, text, update
from sqlalchemy.orm import Session

from app_private.models import (
    ActivitySchedule,
    Category,
    CircleRevision,
    CircleRevisionTag,
    Tag,
)
from app_private.models import (
    Circle as ProductCircle,
)
from circles.repository import CircleRepository
from circles.schemas import CircleListQuery
from database import SessionLocal, engine
from main import app

DATASET_SIZE = 10_000
CONCURRENCY = 50
DEFAULT_SAMPLES = 100
TARGET_P95_MS = 800.0
SLUG_PREFIX = "work2-perf-"
CATEGORY_ID = UUID("30000000-0000-0000-0000-000000000001")
TAG_ID = UUID("30000000-0000-0000-0000-000000000002")
PUBLISHED_BASE = datetime(2026, 1, 1, tzinfo=UTC)


def _circle_id(index: int) -> UUID:
    return uuid5(NAMESPACE_URL, f"campus-circle-work2-performance-circle-{index}")


def _revision_id(index: int) -> UUID:
    return uuid5(NAMESPACE_URL, f"campus-circle-work2-performance-revision-{index}")


def _schedule_id(index: int) -> UUID:
    return uuid5(NAMESPACE_URL, f"campus-circle-work2-performance-schedule-{index}")


def _assert_isolated_test_database(session: Session) -> str:
    database_name = str(session.scalar(text("SELECT current_database()")))
    if not database_name.endswith("_test"):
        raise RuntimeError("performance measurement requires an isolated *_test database")
    return database_name


def _cleanup(session: Session) -> None:
    revision_subquery = text(
        "SELECT revision.id FROM app_private.circle_revisions AS revision "
        "JOIN app_private.circles AS circle ON circle.id = revision.circle_id "
        "WHERE circle.slug LIKE :slug_prefix"
    )
    session.execute(
        text(
            "UPDATE app_private.circles SET published_revision_id = NULL "
            "WHERE slug LIKE :slug_prefix"
        ),
        {"slug_prefix": f"{SLUG_PREFIX}%"},
    )
    for table_name in ("activity_schedules", "circle_revision_tags"):
        session.execute(
            text(
                f"DELETE FROM app_private.{table_name} "
                f"WHERE revision_id IN ({revision_subquery.text})"
            ),
            {"slug_prefix": f"{SLUG_PREFIX}%"},
        )
    session.execute(
        text(f"DELETE FROM app_private.circle_revisions WHERE id IN ({revision_subquery.text})"),
        {"slug_prefix": f"{SLUG_PREFIX}%"},
    )
    session.execute(
        text("DELETE FROM app_private.circles WHERE slug LIKE :slug_prefix"),
        {"slug_prefix": f"{SLUG_PREFIX}%"},
    )
    session.execute(delete(Tag).where(Tag.id == TAG_ID))
    session.execute(delete(Category).where(Category.id == CATEGORY_ID))
    session.commit()


def _seed(session: Session) -> None:
    session.execute(
        insert(Category),
        [
            {
                "id": CATEGORY_ID,
                "name": "Performance",
                "slug": "work2-performance",
                "display_order": 0,
            }
        ],
    )
    session.execute(
        insert(Tag),
        [
            {
                "id": TAG_ID,
                "name": "Performance Filter",
                "slug": "work2-performance",
                "display_order": 0,
            }
        ],
    )

    circle_types = ("circle", "club", "intercollegiate", "student_organization")
    for start in range(0, DATASET_SIZE, 1_000):
        stop = min(start + 1_000, DATASET_SIZE)
        circles: list[dict[str, Any]] = []
        revisions: list[dict[str, Any]] = []
        schedules: list[dict[str, Any]] = []
        revision_tags: list[dict[str, Any]] = []
        publication_links: list[dict[str, UUID]] = []
        for index in range(start, stop):
            circle_id = _circle_id(index)
            revision_id = _revision_id(index)
            is_even = index % 2 == 0
            circles.append(
                {
                    "id": circle_id,
                    "slug": f"{SLUG_PREFIX}{index}",
                    "lifecycle_status": "published",
                    "official_status": "official" if is_even else "unofficial",
                    "verification_type": "public_unverified",
                    "published_revision_id": None,
                    "deleted_at": None,
                }
            )
            revisions.append(
                {
                    "id": revision_id,
                    "circle_id": circle_id,
                    "version_no": 1,
                    "status": "published",
                    "display_name": (
                        f"Performance Target Circle {index}"
                        if index % 10 == 0
                        else f"Benchmark Circle {index}"
                    ),
                    "circle_type": circle_types[index % len(circle_types)],
                    "category_id": CATEGORY_ID,
                    "headline": f"Benchmark headline {index}",
                    "summary": "Public Circle performance dataset",
                    "description": "Deterministic non-production benchmark record",
                    "recruiting_status": "open",
                    "member_count_band": "11_30",
                    "camp_frequency_code": "once_year",
                    "activity_frequency_code": "weekly",
                    "drinking_frequency_rating": 3,
                    "liveliness_rating": 3,
                    "commitment_rating": 3,
                    "attendance_flexibility_rating": 3,
                    "career_opportunity_rating": 3,
                    "gender_balance_code": "balanced" if is_even else "mixed_or_other",
                    "published_at": PUBLISHED_BASE + timedelta(seconds=index),
                }
            )
            schedules.append(
                {
                    "id": _schedule_id(index),
                    "revision_id": revision_id,
                    "weekday": (index % 7) + 1,
                    "time_band": "evening" if is_even else "daytime",
                    "starts_at": None,
                    "ends_at": None,
                    "note": None,
                    "display_order": 0,
                }
            )
            revision_tags.append(
                {
                    "revision_id": revision_id,
                    "tag_id": TAG_ID,
                    "is_featured": True,
                    "display_order": 0,
                }
            )
            publication_links.append({"circle_id": circle_id, "revision_id": revision_id})

        session.execute(insert(ProductCircle), circles)
        session.execute(insert(CircleRevision), revisions)
        session.execute(insert(ActivitySchedule), schedules)
        session.execute(insert(CircleRevisionTag), revision_tags)
        session.execute(
            update(ProductCircle.__table__)
            .where(ProductCircle.__table__.c.id == text(":circle_id"))
            .values(published_revision_id=text(":revision_id")),
            publication_links,
        )
        session.commit()

    session.execute(text("ANALYZE app_private.circles"))
    session.execute(text("ANALYZE app_private.circle_revisions"))
    session.execute(text("ANALYZE app_private.circle_revision_tags"))
    session.execute(text("ANALYZE app_private.activity_schedules"))
    session.commit()


SCENARIOS: dict[str, Sequence[tuple[str, str]]] = {
    "global_newest": (("limit", "20"),),
    "without_q": (("officialStatus", "official"), ("limit", "20")),
    "with_q": (("q", "performance target"), ("limit", "20")),
    "multiple_filters": (
        ("officialStatus", "official"),
        ("circleType", "circle"),
        ("weekday", "1"),
        ("timeBand", "evening"),
        ("tagId", str(TAG_ID)),
        ("genderBalanceCode", "balanced"),
        ("limit", "20"),
    ),
}


def _query_for_scenario(name: str) -> CircleListQuery:
    if name == "global_newest":
        return CircleListQuery(limit=20)
    if name == "without_q":
        return CircleListQuery(official_status=["official"], limit=20)
    if name == "with_q":
        return CircleListQuery(q="performance target", limit=20)
    return CircleListQuery(
        official_status=["official"],
        circle_type=["circle"],
        weekday=["1"],
        time_band=["evening"],
        tag_id=[TAG_ID],
        gender_balance_code=["balanced"],
        limit=20,
    )


def _percentile_95(samples: list[float]) -> float:
    ordered = sorted(samples)
    return ordered[math.ceil(len(ordered) * 0.95) - 1]


async def _measure_scenario(
    client: httpx.AsyncClient,
    params: Sequence[tuple[str, str]],
    *,
    sample_count: int,
) -> dict[str, float | int]:
    for _ in range(5):
        response = await client.get("/api/v1/circles", params=params)
        response.raise_for_status()

    semaphore = asyncio.Semaphore(CONCURRENCY)

    async def request_once() -> float:
        async with semaphore:
            started_at = time.perf_counter()
            response = await client.get("/api/v1/circles", params=params)
            elapsed_ms = (time.perf_counter() - started_at) * 1_000
            response.raise_for_status()
            body = response.json()
            if body["page"]["totalCount"] < len(body["data"]):
                raise AssertionError("totalCount is smaller than the returned page")
            return elapsed_ms

    durations = await asyncio.gather(*(request_once() for _ in range(sample_count)))
    return {
        "samples": sample_count,
        "minMs": round(min(durations), 2),
        "medianMs": round(sorted(durations)[len(durations) // 2], 2),
        "p95Ms": round(_percentile_95(durations), 2),
        "maxMs": round(max(durations), 2),
    }


async def _measure(sample_count: int) -> dict[str, dict[str, float | int]]:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://work2.test") as client:
        return {
            name: await _measure_scenario(client, params, sample_count=sample_count)
            for name, params in SCENARIOS.items()
        }


def _plan_nodes(plan: dict[str, Any]) -> list[str]:
    nodes = [str(plan["Node Type"])]
    for child in plan.get("Plans", []):
        nodes.extend(_plan_nodes(child))
    return nodes


def _explain_statement(session: Session, statement: Any) -> dict[str, Any]:
    compiled = statement.compile(engine, compile_kwargs={"literal_binds": True})
    raw_plan = session.scalar(text(f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {compiled}"))
    parsed = json.loads(raw_plan) if isinstance(raw_plan, str) else raw_plan
    report = parsed[0]
    root = report["Plan"]
    return {
        "planningMs": round(float(report["Planning Time"]), 3),
        "executionMs": round(float(report["Execution Time"]), 3),
        "rootNode": root["Node Type"],
        "actualRows": root["Actual Rows"],
        "nodeTypes": _plan_nodes(root),
    }


def _explain(session: Session) -> dict[str, dict[str, dict[str, Any]]]:
    repository = CircleRepository(session)
    plans: dict[str, dict[str, dict[str, Any]]] = {}
    for name in SCENARIOS:
        query = _query_for_scenario(name)
        filters = query.normalized_filters()
        plans[name] = {
            "count": _explain_statement(session, repository.build_count_statement(filters)),
            "page": _explain_statement(
                session,
                repository.build_list_statement(filters=filters, after=None, limit=query.limit + 1),
            ),
        }
    return plans


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=int, default=DEFAULT_SAMPLES)
    parser.add_argument("--keep-data", action="store_true")
    arguments = parser.parse_args()
    if arguments.samples < CONCURRENCY:
        parser.error(f"--samples must be at least {CONCURRENCY}")

    with SessionLocal() as session:
        database_name = _assert_isolated_test_database(session)
        _cleanup(session)
        try:
            _seed(session)
            measurements = asyncio.run(_measure(arguments.samples))
            plans = _explain(session)
            report = {
                "database": database_name,
                "datasetSize": DATASET_SIZE,
                "concurrency": CONCURRENCY,
                "targetP95Ms": TARGET_P95_MS,
                "measurements": measurements,
                "plans": plans,
            }
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return int(
                any(
                    float(measurement["p95Ms"]) > TARGET_P95_MS
                    for measurement in measurements.values()
                )
            )
        finally:
            if not arguments.keep_data:
                _cleanup(session)


if __name__ == "__main__":
    raise SystemExit(main())
