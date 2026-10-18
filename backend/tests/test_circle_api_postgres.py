import os
from collections.abc import Iterator
from datetime import UTC, datetime, time, timedelta
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, insert, text, update
from sqlalchemy.orm import Session

from app_private.models import (
    ActivityLocation,
    ActivitySchedule,
    Campus,
    Category,
    CircleCost,
    CircleRevision,
    CircleRevisionTag,
    CircleUniversity,
    Tag,
    University,
)
from app_private.models import (
    Circle as ProductCircle,
)
from circles.cursor import CURSOR_SECRET_ENV
from database import Base, SessionLocal, engine
from main import app
from seed import seed_database

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_POSTGRES_INTEGRATION") != "1",
    reason="set RUN_POSTGRES_INTEGRATION=1 against an isolated *_test PostgreSQL database",
)

CATEGORY_ID = UUID("20000000-0000-0000-0000-000000000001")
UNIVERSITY_ID = UUID("20000000-0000-0000-0000-000000000002")
CAMPUS_ID = UUID("20000000-0000-0000-0000-000000000003")
TAG_IDS = tuple(UUID(f"20000000-0000-0000-0000-{index:012d}") for index in range(10, 17))
CIRCLE_IDS = tuple(UUID(f"20000000-0000-0000-0000-{index:012d}") for index in range(101, 113))
REVISION_IDS = tuple(UUID(f"20000000-0000-0000-0000-{index:012d}") for index in range(201, 212))
SCHEDULE_IDS = tuple(UUID(f"20000000-0000-0000-0000-{index:012d}") for index in range(301, 304))
LOCATION_ID = UUID("20000000-0000-0000-0000-000000000401")
COST_IDS = (
    UUID("20000000-0000-0000-0000-000000000501"),
    UUID("20000000-0000-0000-0000-000000000502"),
)
TRANSIENT_CIRCLE_ID = UUID("20000000-0000-0000-0000-000000000901")
TRANSIENT_REVISION_ID = UUID("20000000-0000-0000-0000-000000000902")
KEYSET_CIRCLE_IDS = tuple(
    UUID(f"20000000-0000-0000-0000-{index:012d}") for index in range(951, 956)
)
KEYSET_REVISION_IDS = tuple(
    UUID(f"20000000-0000-0000-0000-{index:012d}") for index in range(961, 966)
)
KEYSET_QUERY = "Keyset Boundary Fixture"

PUBLISHED_AT = datetime(2026, 9, 18, 12, 0, tzinfo=UTC)
OLDER_PUBLISHED_AT = datetime(2026, 9, 17, 12, 0, tzinfo=UTC)
KEYSET_SHARED_PUBLISHED_AT = PUBLISHED_AT + timedelta(days=2)
KEYSET_OLDER_PUBLISHED_AT = PUBLISHED_AT + timedelta(days=1)


def _revision(
    revision_id: UUID,
    circle_id: UUID,
    *,
    status: str = "published",
    display_name: str,
    circle_type: str = "circle",
    published_at: datetime | None = PUBLISHED_AT,
    version_no: int = 1,
    headline: str = "カード用キャッチコピー",
    summary: str = "主な活動内容・短い紹介",
    description: str = "公開詳細説明",
    recruiting_status: str = "open",
    member_count_band: str | None = "11_30",
    camp_frequency_code: str | None = "once_year",
    activity_frequency_code: str | None = "weekly",
    gender_balance_code: str | None = "balanced",
) -> dict[str, object]:
    return {
        "id": revision_id,
        "circle_id": circle_id,
        "version_no": version_no,
        "status": status,
        "display_name": display_name,
        "circle_type": circle_type,
        "category_id": CATEGORY_ID,
        "headline": headline,
        "summary": summary,
        "description": description,
        "recruiting_status": recruiting_status,
        "member_count_band": member_count_band,
        "camp_frequency_code": camp_frequency_code,
        "activity_frequency_code": activity_frequency_code,
        "drinking_frequency_rating": 2 if member_count_band is not None else None,
        "liveliness_rating": 3 if member_count_band is not None else None,
        "commitment_rating": 4 if member_count_band is not None else None,
        "attendance_flexibility_rating": 5 if member_count_band is not None else None,
        "career_opportunity_rating": 1 if member_count_band is not None else None,
        "gender_balance_code": gender_balance_code,
        "published_at": published_at,
    }


def _circle(
    circle_id: UUID,
    *,
    lifecycle_status: str = "published",
    official_status: str = "official",
    deleted_at: datetime | None = None,
) -> dict[str, object]:
    return {
        "id": circle_id,
        "slug": f"work2-{circle_id}",
        "lifecycle_status": lifecycle_status,
        "official_status": official_status,
        "verification_type": "public_unverified",
        "published_revision_id": None,
        "deleted_at": deleted_at,
    }


def _cleanup_fixture(session: Session) -> None:
    # D4 rows reference the shared category, so remove them first.
    _cleanup_schedule_fixture(session)
    all_circle_ids = (*CIRCLE_IDS, TRANSIENT_CIRCLE_ID, *KEYSET_CIRCLE_IDS)
    all_revision_ids = (*REVISION_IDS, TRANSIENT_REVISION_ID, *KEYSET_REVISION_IDS)
    session.execute(
        update(ProductCircle)
        .where(ProductCircle.id.in_(all_circle_ids))
        .values(published_revision_id=None)
    )
    session.execute(delete(CircleCost).where(CircleCost.revision_id.in_(all_revision_ids)))
    session.execute(
        delete(ActivityLocation).where(ActivityLocation.revision_id.in_(all_revision_ids))
    )
    session.execute(
        delete(ActivitySchedule).where(ActivitySchedule.revision_id.in_(all_revision_ids))
    )
    session.execute(
        delete(CircleRevisionTag).where(CircleRevisionTag.revision_id.in_(all_revision_ids))
    )
    session.execute(delete(CircleRevision).where(CircleRevision.id.in_(all_revision_ids)))
    session.execute(delete(CircleUniversity).where(CircleUniversity.circle_id.in_(all_circle_ids)))
    session.execute(delete(ProductCircle).where(ProductCircle.id.in_(all_circle_ids)))
    session.execute(delete(Campus).where(Campus.id == CAMPUS_ID))
    session.execute(delete(University).where(University.id == UNIVERSITY_ID))
    session.execute(delete(Tag).where(Tag.id.in_(TAG_IDS)))
    session.execute(delete(Category).where(Category.id == CATEGORY_ID))
    session.commit()


@pytest.fixture(scope="module", autouse=True)
def postgres_fixture() -> Iterator[None]:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        database_name = session.scalar(text("SELECT current_database()"))
        if not str(database_name).endswith("_test"):
            pytest.fail("PostgreSQL integration tests require an isolated *_test database")
        _cleanup_fixture(session)
        seed_database(session)
        session.execute(
            insert(Category),
            [{"id": CATEGORY_ID, "name": "音楽", "slug": "music", "display_order": 0}],
        )
        session.execute(
            insert(University),
            [{"id": UNIVERSITY_ID, "name": "法政大学", "slug": "hosei"}],
        )
        session.execute(
            insert(Campus),
            [
                {
                    "id": CAMPUS_ID,
                    "university_id": UNIVERSITY_ID,
                    "name": "市ヶ谷キャンパス",
                    "slug": "ichigaya",
                }
            ],
        )
        session.execute(
            insert(Tag),
            [
                {
                    "id": tag_id,
                    "name": "初心者歓迎" if index == 0 else f"表示タグ{index + 1}",
                    "slug": f"work2-tag-{index + 1}",
                    "display_order": index,
                }
                for index, tag_id in enumerate(TAG_IDS)
            ],
        )
        circles = [
            _circle(CIRCLE_IDS[0]),
            _circle(CIRCLE_IDS[1], official_status="unofficial"),
            _circle(CIRCLE_IDS[2]),
            _circle(CIRCLE_IDS[3], official_status="unknown"),
            _circle(CIRCLE_IDS[4], lifecycle_status="draft"),
            _circle(CIRCLE_IDS[5], lifecycle_status="suspended"),
            _circle(CIRCLE_IDS[6], deleted_at=datetime(2026, 9, 18, tzinfo=UTC)),
            _circle(CIRCLE_IDS[7]),
            _circle(CIRCLE_IDS[8]),
            _circle(CIRCLE_IDS[9]),
            _circle(CIRCLE_IDS[10]),
            _circle(CIRCLE_IDS[11]),
        ]
        session.execute(insert(ProductCircle), circles)
        revisions = [
            _revision(
                REVISION_IDS[0],
                CIRCLE_IDS[0],
                display_name="100%_Music Circle",
                headline="ロボティクスも扱うキャッチコピー",
                summary="A専用サマリー検索語",
                description="検索専用の詳細キーワード",
            ),
            _revision(
                REVISION_IDS[1],
                CIRCLE_IDS[1],
                display_name="100ABMusic Club",
                circle_type="club",
                member_count_band="31_80",
                camp_frequency_code="twice_year",
                activity_frequency_code="two_three_weekly",
                gender_balance_code="women_majority",
            ),
            _revision(
                REVISION_IDS[2],
                CIRCLE_IDS[2],
                display_name="Older Intercollegiate",
                circle_type="intercollegiate",
                published_at=OLDER_PUBLISHED_AT,
                member_count_band="81_150",
                camp_frequency_code="none",
                activity_frequency_code="monthly",
                gender_balance_code="men_majority",
            ),
            _revision(
                REVISION_IDS[3],
                CIRCLE_IDS[3],
                display_name="Nullable Published Circle",
                circle_type="student_organization",
                published_at=None,
                recruiting_status="unknown",
                member_count_band=None,
                camp_frequency_code=None,
                activity_frequency_code=None,
                gender_balance_code=None,
            ),
            _revision(REVISION_IDS[4], CIRCLE_IDS[4], display_name="Draft Circle"),
            _revision(REVISION_IDS[5], CIRCLE_IDS[5], display_name="Suspended Circle"),
            _revision(REVISION_IDS[6], CIRCLE_IDS[6], display_name="Deleted Circle"),
            _revision(
                REVISION_IDS[7],
                CIRCLE_IDS[7],
                status="draft",
                display_name="Only Draft Revision",
                published_at=None,
            ),
            _revision(
                REVISION_IDS[8],
                CIRCLE_IDS[8],
                display_name="Published Revision Wins",
                published_at=OLDER_PUBLISHED_AT - timedelta(days=1),
                member_count_band="151_plus",
                camp_frequency_code="three_plus_year",
                activity_frequency_code="four_plus_weekly",
                gender_balance_code="mixed_or_other",
            ),
            _revision(
                REVISION_IDS[9],
                CIRCLE_IDS[8],
                status="draft",
                display_name="DO-NOT-LEAK-DRAFT",
                published_at=None,
                version_no=2,
            ),
            _revision(
                REVISION_IDS[10],
                CIRCLE_IDS[11],
                status="in_review",
                display_name="Review Only Revision",
                published_at=None,
            ),
        ]
        session.execute(insert(CircleRevision), revisions)
        for circle_id, revision_id in zip(CIRCLE_IDS[:8], REVISION_IDS[:8], strict=True):
            session.execute(
                update(ProductCircle)
                .where(ProductCircle.id == circle_id)
                .values(published_revision_id=revision_id)
            )
        session.execute(
            update(ProductCircle)
            .where(ProductCircle.id == CIRCLE_IDS[8])
            .values(published_revision_id=REVISION_IDS[8])
        )
        session.execute(
            update(ProductCircle)
            .where(ProductCircle.id == CIRCLE_IDS[10])
            .values(published_revision_id=REVISION_IDS[0])
        )
        session.execute(
            update(ProductCircle)
            .where(ProductCircle.id == CIRCLE_IDS[11])
            .values(published_revision_id=REVISION_IDS[10])
        )
        session.execute(
            insert(CircleUniversity),
            [
                {
                    "circle_id": CIRCLE_IDS[0],
                    "university_id": UNIVERSITY_ID,
                    "campus_id": CAMPUS_ID,
                    "relationship_type": "primary",
                }
            ],
        )
        session.execute(
            insert(CircleRevisionTag),
            [
                {
                    "revision_id": REVISION_IDS[0],
                    "tag_id": tag_id,
                    "is_featured": index < 6,
                    "display_order": index,
                }
                for index, tag_id in enumerate(TAG_IDS)
            ],
        )
        session.execute(
            insert(ActivitySchedule),
            [
                {
                    "id": SCHEDULE_IDS[0],
                    "revision_id": REVISION_IDS[0],
                    "weekday": 1,
                    "time_band": "evening",
                    "starts_at": time(18, 0),
                    "ends_at": time(20, 0),
                    "note": "毎週",
                    "display_order": 0,
                },
                {
                    "id": SCHEDULE_IDS[1],
                    "revision_id": REVISION_IDS[0],
                    "weekday": None,
                    "time_band": "irregular",
                    "starts_at": None,
                    "ends_at": None,
                    "note": None,
                    "display_order": 1,
                },
                {
                    "id": SCHEDULE_IDS[2],
                    "revision_id": REVISION_IDS[1],
                    "weekday": 2,
                    "time_band": "night",
                    "starts_at": None,
                    "ends_at": None,
                    "note": None,
                    "display_order": 0,
                },
            ],
        )
        session.execute(
            insert(ActivityLocation),
            [
                {
                    "id": LOCATION_ID,
                    "revision_id": REVISION_IDS[0],
                    "prefecture": "東京都",
                    "city": "千代田区",
                    "facility_name": "外濠校舎",
                    "nearest_station": "市ケ谷駅",
                    "is_online": True,
                    "public_note": "正門前ではなくオンライン併用",
                    "display_order": 0,
                }
            ],
        )
        session.execute(
            insert(CircleCost),
            [
                {
                    "id": COST_IDS[0],
                    "revision_id": REVISION_IDS[0],
                    "cost_type": "annual",
                    "amount_min_yen": 1000,
                    "amount_max_yen": 2000,
                    "label": "年会費",
                    "note": None,
                    "display_order": 0,
                },
                {
                    "id": COST_IDS[1],
                    "revision_id": REVISION_IDS[0],
                    "cost_type": "per_event",
                    "amount_min_yen": 0,
                    "amount_max_yen": None,
                    "label": "参加費",
                    "note": "イベントによる",
                    "display_order": 1,
                },
            ],
        )
        session.commit()

    yield

    with SessionLocal() as session:
        _cleanup_fixture(session)


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app, raise_server_exceptions=False)


def _ids(response) -> list[str]:
    assert response.status_code == 200, response.text
    return [item["id"] for item in response.json()["data"]]


def test_list_visibility_shape_order_nullable_and_featured_limit(client: TestClient) -> None:
    response = client.get("/api/v1/circles", params={"limit": 50})
    body = response.json()

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert _ids(response) == [
        str(CIRCLE_IDS[1]),
        str(CIRCLE_IDS[0]),
        str(CIRCLE_IDS[2]),
        str(CIRCLE_IDS[8]),
        str(CIRCLE_IDS[3]),
    ]
    assert body["page"] == {"hasMore": False, "limit": 50, "totalCount": 5}
    assert UUID(body["meta"]["requestId"])
    first = body["data"][1]
    assert set(first) == {
        "id",
        "displayName",
        "headline",
        "summary",
        "officialStatus",
        "circleType",
        "publishedAt",
        "category",
        "universities",
        "featuredTags",
        "activitySchedules",
        "activityLocations",
    }
    assert first["publishedAt"] == "2026-09-18T12:00:00Z"
    assert first["universities"][0]["campus"] == "市ヶ谷キャンパス"
    assert [tag["name"] for tag in first["featuredTags"]] == [
        "初心者歓迎",
        "表示タグ2",
        "表示タグ3",
        "表示タグ4",
        "表示タグ5",
    ]
    assert len(first["featuredTags"]) == 5
    assert [schedule["weekday"] for schedule in first["activitySchedules"]] == [
        "1",
        "irregular",
    ]
    assert body["data"][-1]["publishedAt"] is None


def test_detail_uses_only_the_published_revision_and_exact_public_shape(
    client: TestClient,
) -> None:
    response = client.get(f"/api/v1/circles/{CIRCLE_IDS[0]}")
    body = response.json()

    assert response.status_code == 200
    data = body["data"]
    assert data["displayName"] == "100%_Music Circle"
    assert data["description"] == "検索専用の詳細キーワード"
    assert data["genderBalanceCode"] == "balanced"
    assert len(data["tags"]) == 7
    assert data["tags"][0]["isFeatured"] is True
    assert data["costs"] == [
        {
            "costType": "annual",
            "amountMinYen": 1000,
            "amountMaxYen": 2000,
            "label": "年会費",
            "note": None,
        },
        {
            "costType": "per_event",
            "amountMinYen": 0,
            "amountMaxYen": None,
            "label": "参加費",
            "note": "イベントによる",
        },
    ]
    forbidden = {
        "slug",
        "socialLinks",
        "media",
        "images",
        "revisionId",
        "lifecycleStatus",
        "verificationType",
    }
    assert forbidden.isdisjoint(data)
    assert UUID(body["meta"]["requestId"])


@pytest.mark.parametrize(
    "circle_id",
    [*CIRCLE_IDS[4:8], *CIRCLE_IDS[9:12], UUID(int=999)],
)
def test_detail_non_disclosure_returns_the_same_404(
    client: TestClient,
    circle_id: UUID,
) -> None:
    response = client.get(f"/api/v1/circles/{circle_id}")

    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["code"] == "NOT_FOUND"


def test_malformed_circle_id_is_a_422_problem_details(client: TestClient) -> None:
    response = client.get("/api/v1/circles/not-a-uuid")

    assert response.status_code == 422
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["code"] == "VALIDATION_ERROR"
    assert response.json()["errors"][0]["field"] == "circleId"


@pytest.mark.parametrize(
    ("parameter", "value", "expected"),
    [
        ("officialStatus", "unofficial", CIRCLE_IDS[1]),
        ("circleType", "club", CIRCLE_IDS[1]),
        ("campFrequencyCode", "once_year", CIRCLE_IDS[0]),
        ("memberCountBand", "11_30", CIRCLE_IDS[0]),
        ("activityFrequencyCode", "weekly", CIRCLE_IDS[0]),
        ("weekday", "1", CIRCLE_IDS[0]),
        ("weekday", "irregular", CIRCLE_IDS[0]),
        ("timeBand", "evening", CIRCLE_IDS[0]),
        ("tagId", str(TAG_IDS[0]), CIRCLE_IDS[0]),
        ("genderBalanceCode", "balanced", CIRCLE_IDS[0]),
    ],
)
def test_each_approved_structured_filter(
    client: TestClient,
    parameter: str,
    value: str,
    expected: UUID,
) -> None:
    response = client.get("/api/v1/circles", params=[(parameter, value), ("limit", "50")])

    assert _ids(response) == [str(expected)]
    assert response.json()["page"]["totalCount"] == 1


def test_same_filter_is_or_and_cross_filters_are_and(client: TestClient) -> None:
    same_filter = client.get(
        "/api/v1/circles",
        params=[
            ("officialStatus", "official"),
            ("officialStatus", "unofficial"),
            ("limit", "50"),
        ],
    )
    cross_filter = client.get(
        "/api/v1/circles",
        params=[("officialStatus", "official"), ("circleType", "circle"), ("limit", "50")],
    )
    tag_or = client.get(
        "/api/v1/circles",
        params=[("tagId", str(TAG_IDS[0])), ("tagId", str(TAG_IDS[6]))],
    )

    assert str(CIRCLE_IDS[0]) in _ids(same_filter)
    assert str(CIRCLE_IDS[1]) in _ids(same_filter)
    assert _ids(cross_filter) == [str(CIRCLE_IDS[0]), str(CIRCLE_IDS[8])]
    assert _ids(tag_or) == [str(CIRCLE_IDS[0])]


@pytest.mark.parametrize(
    "query",
    [
        "100%_Music",
        "ロボティクス",
        "A専用サマリー",
        "検索専用",
        "法政大学",
        "市ヶ谷キャンパス",
        "初心者歓迎",
        "東京都",
        "千代田区",
        "外濠校舎",
        "市ケ谷駅",
        "オンライン併用",
    ],
)
def test_q_searches_every_approved_field_and_escapes_wildcards(
    client: TestClient,
    query: str,
) -> None:
    response = client.get("/api/v1/circles", params={"q": query, "limit": 50})
    assert _ids(response) == [str(CIRCLE_IDS[0])]


def test_q_is_and_with_structured_filters_and_does_not_search_drafts(
    client: TestClient,
) -> None:
    matched = client.get(
        "/api/v1/circles",
        params={"q": "100%_Music", "officialStatus": "official"},
    )
    excluded = client.get(
        "/api/v1/circles",
        params={"q": "100%_Music", "officialStatus": "unofficial"},
    )
    draft = client.get("/api/v1/circles", params={"q": "DO-NOT-LEAK-DRAFT"})
    review = client.get("/api/v1/circles", params={"q": "Review Only Revision"})
    injection = client.get("/api/v1/circles", params={"q": "' OR 1=1 --"})

    assert _ids(matched) == [str(CIRCLE_IDS[0])]
    assert _ids(excluded) == []
    assert _ids(draft) == []
    assert _ids(review) == []
    assert _ids(injection) == []


@pytest.mark.parametrize(
    "params",
    [
        {"q": "   "},
        {"limit": 0},
        {"limit": 51},
        {"sort": "recommended"},
        {"weekday": "0"},
    ],
)
def test_query_validation_is_422_problem_details(client: TestClient, params: dict) -> None:
    response = client.get("/api/v1/circles", params=params)
    assert response.status_code == 422
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["code"] == "VALIDATION_ERROR"


def test_keyset_pagination_is_stable_and_total_count_precedes_cursor(client: TestClient) -> None:
    first = client.get("/api/v1/circles", params={"limit": 2})
    first_body = first.json()
    second = client.get(
        "/api/v1/circles",
        params={"limit": 2, "cursor": first_body["page"]["nextCursor"]},
    )
    second_body = second.json()
    final = client.get(
        "/api/v1/circles",
        params={"limit": 2, "cursor": second_body["page"]["nextCursor"]},
    )

    assert _ids(first) == [str(CIRCLE_IDS[1]), str(CIRCLE_IDS[0])]
    assert _ids(second) == [str(CIRCLE_IDS[2]), str(CIRCLE_IDS[8])]
    assert _ids(final) == [str(CIRCLE_IDS[3])]
    combined = [*_ids(first), *_ids(second), *_ids(final)]
    assert len(combined) == len(set(combined)) == 5
    assert first_body["page"]["totalCount"] == 5
    assert second_body["page"]["totalCount"] == 5
    assert final.json()["page"] == {"hasMore": False, "limit": 2, "totalCount": 5}


def test_keyset_crosses_equal_timestamp_and_nullable_boundaries_without_gaps(
    client: TestClient,
) -> None:
    fixture_rows = [
        (
            KEYSET_CIRCLE_IDS[4],
            KEYSET_REVISION_IDS[4],
            KEYSET_SHARED_PUBLISHED_AT,
        ),
        (
            KEYSET_CIRCLE_IDS[3],
            KEYSET_REVISION_IDS[3],
            KEYSET_SHARED_PUBLISHED_AT,
        ),
        (
            KEYSET_CIRCLE_IDS[2],
            KEYSET_REVISION_IDS[2],
            KEYSET_OLDER_PUBLISHED_AT,
        ),
        (KEYSET_CIRCLE_IDS[1], KEYSET_REVISION_IDS[1], None),
        (KEYSET_CIRCLE_IDS[0], KEYSET_REVISION_IDS[0], None),
    ]
    with SessionLocal() as session:
        session.execute(
            insert(ProductCircle),
            [_circle(circle_id) for circle_id, _, _ in fixture_rows],
        )
        session.execute(
            insert(CircleRevision),
            [
                _revision(
                    revision_id,
                    circle_id,
                    display_name=f"{KEYSET_QUERY} {index}",
                    published_at=published_at,
                )
                for index, (circle_id, revision_id, published_at) in enumerate(fixture_rows)
            ],
        )
        for circle_id, revision_id, _ in fixture_rows:
            session.execute(
                update(ProductCircle)
                .where(ProductCircle.id == circle_id)
                .values(published_revision_id=revision_id)
            )
        session.commit()

    try:
        pages: list[dict] = []
        request_cursors: list[str | None] = []
        cursor: str | None = None
        for _ in range(6):
            request_cursors.append(cursor)
            params: dict[str, str | int] = {"q": KEYSET_QUERY, "limit": 1}
            if cursor is not None:
                params["cursor"] = cursor
            response = client.get("/api/v1/circles", params=params)
            assert response.status_code == 200
            body = response.json()
            pages.append(body)
            if not body["page"]["hasMore"]:
                break
            cursor = body["page"]["nextCursor"]
        else:
            pytest.fail("keyset pagination did not terminate")

        expected_ids = [str(circle_id) for circle_id, _, _ in fixture_rows]
        actual_ids = [page["data"][0]["id"] for page in pages]
        assert actual_ids == expected_ids
        assert len(actual_ids) == len(set(actual_ids)) == len(expected_ids)
        assert all(page["page"]["totalCount"] == len(expected_ids) for page in pages)

        assert pages[0]["data"][0]["publishedAt"] == pages[1]["data"][0]["publishedAt"]
        assert UUID(actual_ids[0]) > UUID(actual_ids[1])
        assert pages[2]["data"][0]["publishedAt"] is not None
        assert pages[3]["data"][0]["publishedAt"] is None

        null_position_cursor = pages[3]["page"]["nextCursor"]
        assert request_cursors[4] == null_position_cursor
        assert pages[4]["data"][0]["publishedAt"] is None
        assert UUID(actual_ids[3]) > UUID(actual_ids[4])
        assert pages[4]["page"] == {
            "hasMore": False,
            "limit": 1,
            "totalCount": len(expected_ids),
        }
    finally:
        with SessionLocal() as session:
            session.execute(
                update(ProductCircle)
                .where(ProductCircle.id.in_(KEYSET_CIRCLE_IDS))
                .values(published_revision_id=None)
            )
            session.execute(
                delete(CircleRevision).where(CircleRevision.id.in_(KEYSET_REVISION_IDS))
            )
            session.execute(delete(ProductCircle).where(ProductCircle.id.in_(KEYSET_CIRCLE_IDS)))
            session.commit()


def test_cursor_rejects_tampering_and_filter_mismatch(client: TestClient) -> None:
    first = client.get("/api/v1/circles", params={"limit": 1})
    cursor = first.json()["page"]["nextCursor"]
    replacement = "A" if cursor[-1] != "A" else "B"

    tampered = client.get(
        "/api/v1/circles", params={"limit": 1, "cursor": cursor[:-1] + replacement}
    )
    mismatch = client.get(
        "/api/v1/circles",
        params={"limit": 1, "cursor": cursor, "officialStatus": "official"},
    )

    for response in (tampered, mismatch):
        assert response.status_code == 400
        assert response.headers["content-type"].startswith("application/problem+json")
        assert response.json()["code"] == "INVALID_CURSOR"
        assert "signature" not in response.text.lower()


def test_keyset_handles_new_rows_and_visibility_changes_without_duplicates(
    client: TestClient,
) -> None:
    first = client.get("/api/v1/circles", params={"limit": 2})
    cursor = first.json()["page"]["nextCursor"]
    with SessionLocal() as session:
        session.execute(insert(ProductCircle), [_circle(TRANSIENT_CIRCLE_ID)])
        session.execute(
            insert(CircleRevision),
            [
                _revision(
                    TRANSIENT_REVISION_ID,
                    TRANSIENT_CIRCLE_ID,
                    display_name="Inserted After Page One",
                    published_at=PUBLISHED_AT + timedelta(days=1),
                )
            ],
        )
        session.execute(
            update(ProductCircle)
            .where(ProductCircle.id == TRANSIENT_CIRCLE_ID)
            .values(published_revision_id=TRANSIENT_REVISION_ID)
        )
        session.execute(
            update(ProductCircle)
            .where(ProductCircle.id == CIRCLE_IDS[2])
            .values(lifecycle_status="archived")
        )
        session.commit()
    try:
        second = client.get("/api/v1/circles", params={"limit": 50, "cursor": cursor})
        assert str(TRANSIENT_CIRCLE_ID) not in _ids(second)
        assert str(CIRCLE_IDS[2]) not in _ids(second)
        assert set(_ids(first)).isdisjoint(_ids(second))
        assert second.json()["page"]["totalCount"] == 5
    finally:
        with SessionLocal() as session:
            session.execute(
                update(ProductCircle)
                .where(ProductCircle.id == CIRCLE_IDS[2])
                .values(lifecycle_status="published")
            )
            session.execute(
                update(ProductCircle)
                .where(ProductCircle.id == TRANSIENT_CIRCLE_ID)
                .values(published_revision_id=None)
            )
            session.execute(
                delete(CircleRevision).where(CircleRevision.id == TRANSIENT_REVISION_ID)
            )
            session.execute(delete(ProductCircle).where(ProductCircle.id == TRANSIENT_CIRCLE_ID))
            session.commit()


def test_empty_collection_and_prototype_endpoints_remain_compatible(client: TestClient) -> None:
    empty = client.get("/api/v1/circles", params={"q": "no-match-work2"})
    circles = client.get("/api/circles")
    events = client.get("/api/events")

    assert empty.status_code == 200
    assert empty.json()["data"] == []
    assert empty.json()["page"] == {"hasMore": False, "limit": 20, "totalCount": 0}
    assert circles.status_code == 200
    assert events.status_code == 200
    assert isinstance(circles.json(), list)
    assert isinstance(events.json(), list)


def test_missing_cursor_secret_only_disables_formal_circle_reads(monkeypatch) -> None:
    monkeypatch.delenv(CURSOR_SECRET_ENV, raising=False)

    with TestClient(app, raise_server_exceptions=False) as secretless_client:
        for path in ("/health", "/api/circles", "/api/events", "/api/v1/health"):
            response = secretless_client.get(path)
            assert response.status_code == 200

        circle_response = secretless_client.get("/api/v1/circles")

    assert circle_response.status_code == 500
    assert circle_response.headers["content-type"].startswith("application/problem+json")
    assert circle_response.json()["code"] == "INTERNAL_SERVER_ERROR"
    assert CURSOR_SECRET_ENV not in circle_response.text
    assert "Traceback" not in circle_response.text
    assert "/Users/" not in circle_response.text
    assert "backend/circles" not in circle_response.text


# DEC-066 D4: activity weekday / timeBand search semantics. The fixture rows are
# isolated by their own ids and display-name prefix, are created only for the
# TestActivityScheduleSearch class, and are removed after it (and by
# _cleanup_fixture), so the expectations of the other tests are not affected.
D4_QUERY = "D4 Schedule Fixture"
D4_KEYS = (
    "mon_morning_tue_night",
    "mon_all_day",
    "mon_morning_tue_all_day",
    "mon_night",
    "irregular_only",
    "null_weekday_night",
    "mon_irregular",
    "no_schedule",
    "unpublished_night",
    "wed_evening_sat_daytime",
)
D4_CIRCLE_IDS = {
    key: UUID(f"20000000-0000-0000-0000-{1101 + index:012d}") for index, key in enumerate(D4_KEYS)
}
D4_REVISION_IDS = {
    key: UUID(f"20000000-0000-0000-0000-{1201 + index:012d}") for index, key in enumerate(D4_KEYS)
}
D4_DRAFT_REVISION_ID = UUID("20000000-0000-0000-0000-000000001299")
D4_ALL_REVISION_IDS = (*D4_REVISION_IDS.values(), D4_DRAFT_REVISION_ID)
# (revision key, weekday, time_band); weekday None is the irregular weekday.
D4_SCHEDULES: tuple[tuple[str, int | None, str], ...] = (
    ("mon_morning_tue_night", 1, "morning"),
    ("mon_morning_tue_night", 2, "night"),
    ("mon_all_day", 1, "all_day"),
    # A second matching row on the same revision must not duplicate the Circle.
    ("mon_all_day", 1, "night"),
    ("mon_morning_tue_all_day", 1, "morning"),
    ("mon_morning_tue_all_day", 2, "all_day"),
    ("mon_night", 1, "night"),
    ("irregular_only", None, "irregular"),
    ("null_weekday_night", None, "night"),
    ("mon_irregular", 1, "irregular"),
    ("unpublished_night", 1, "morning"),
    ("wed_evening_sat_daytime", 3, "evening"),
    ("wed_evening_sat_daytime", 6, "daytime"),
)


def _cleanup_schedule_fixture(session: Session) -> None:
    circle_ids = tuple(D4_CIRCLE_IDS.values())
    session.execute(
        update(ProductCircle)
        .where(ProductCircle.id.in_(circle_ids))
        .values(published_revision_id=None)
    )
    session.execute(
        delete(ActivitySchedule).where(ActivitySchedule.revision_id.in_(D4_ALL_REVISION_IDS))
    )
    session.execute(delete(CircleRevision).where(CircleRevision.id.in_(D4_ALL_REVISION_IDS)))
    session.execute(delete(ProductCircle).where(ProductCircle.id.in_(circle_ids)))
    session.commit()


def _d4(*keys: str) -> set[str]:
    return {str(D4_CIRCLE_IDS[key]) for key in keys}


def _d4_search(client: TestClient, params: list[tuple[str, str]], **extra: str):
    query = [("q", D4_QUERY), ("limit", "50"), *params, *extra.items()]
    return client.get("/api/v1/circles", params=query)


def _assert_d4_result(response, expected: set[str]) -> None:
    ids = _ids(response)
    assert len(ids) == len(set(ids)), "a Circle must not be duplicated"
    assert set(ids) == expected
    assert response.json()["page"]["totalCount"] == len(expected)


@pytest.fixture(scope="class")
def schedule_fixture() -> Iterator[None]:
    with SessionLocal() as session:
        _cleanup_schedule_fixture(session)
        session.execute(
            insert(ProductCircle),
            [
                _circle(
                    D4_CIRCLE_IDS[key],
                    official_status="unofficial" if key == "mon_night" else "official",
                )
                for key in D4_KEYS
            ],
        )
        session.execute(
            insert(CircleRevision),
            [
                _revision(
                    D4_REVISION_IDS[key],
                    D4_CIRCLE_IDS[key],
                    display_name=f"{D4_QUERY} {key}",
                    published_at=PUBLISHED_AT - timedelta(days=10, minutes=index),
                )
                for index, key in enumerate(D4_KEYS)
            ]
            + [
                _revision(
                    D4_DRAFT_REVISION_ID,
                    D4_CIRCLE_IDS["unpublished_night"],
                    status="draft",
                    display_name=f"{D4_QUERY} unpublished draft",
                    published_at=None,
                    version_no=2,
                )
            ],
        )
        for key in D4_KEYS:
            session.execute(
                update(ProductCircle)
                .where(ProductCircle.id == D4_CIRCLE_IDS[key])
                .values(published_revision_id=D4_REVISION_IDS[key])
            )
        schedule_rows = [
            {
                "id": UUID(f"20000000-0000-0000-0000-{1301 + index:012d}"),
                "revision_id": D4_REVISION_IDS[key],
                "weekday": weekday,
                "time_band": time_band,
                "starts_at": None,
                "ends_at": None,
                "note": None,
                "display_order": index,
            }
            for index, (key, weekday, time_band) in enumerate(D4_SCHEDULES)
        ]
        # The draft (unpublished) revision has a Monday-night row that must never match.
        schedule_rows.append(
            {
                "id": UUID("20000000-0000-0000-0000-000000001399"),
                "revision_id": D4_DRAFT_REVISION_ID,
                "weekday": 1,
                "time_band": "night",
                "starts_at": None,
                "ends_at": None,
                "note": None,
                "display_order": 0,
            }
        )
        session.execute(insert(ActivitySchedule), schedule_rows)
        session.commit()

    yield

    with SessionLocal() as session:
        _cleanup_schedule_fixture(session)


REGULAR_BANDS = ("morning", "daytime", "evening", "night")


@pytest.mark.usefixtures("schedule_fixture")
class TestActivityScheduleSearch:
    @pytest.mark.parametrize(
        ("params", "expected_keys"),
        [
            # Weekday and timeBand must match on the same schedule row.
            ([("weekday", "1"), ("timeBand", "night")], ("mon_all_day", "mon_night")),
            ([("weekday", "1"), ("timeBand", "all_day")], ("mon_all_day",)),
            ([("weekday", "2"), ("timeBand", "morning")], ("mon_morning_tue_all_day",)),
            # all_day matches each regular band, but all_day alone does not widen.
            ([("timeBand", "all_day")], ("mon_all_day", "mon_morning_tue_all_day")),
            (
                [("timeBand", "night")],
                (
                    "mon_morning_tue_night",
                    "mon_all_day",
                    "mon_morning_tue_all_day",
                    "mon_night",
                    "null_weekday_night",
                ),
            ),
            # irregular matches only itself.
            ([("timeBand", "irregular")], ("irregular_only", "mon_irregular")),
            (
                [("timeBand", "night"), ("timeBand", "irregular")],
                (
                    "mon_morning_tue_night",
                    "mon_all_day",
                    "mon_morning_tue_all_day",
                    "mon_night",
                    "null_weekday_night",
                    "irregular_only",
                    "mon_irregular",
                ),
            ),
            # weekday=irregular is the NULL weekday.
            ([("weekday", "irregular"), ("timeBand", "night")], ("null_weekday_night",)),
            ([("weekday", "irregular")], ("irregular_only", "null_weekday_night")),
            # Weekday only: no implicit time-band restriction.
            (
                [("weekday", "1")],
                (
                    "mon_morning_tue_night",
                    "mon_all_day",
                    "mon_morning_tue_all_day",
                    "mon_night",
                    "mon_irregular",
                    "unpublished_night",
                ),
            ),
            # Same filter OR, different filters AND.
            (
                [
                    ("weekday", "1"),
                    ("weekday", "3"),
                    ("timeBand", "evening"),
                    ("timeBand", "daytime"),
                ],
                ("mon_all_day", "wed_evening_sat_daytime"),
            ),
            (
                [("weekday", "2"), ("weekday", "6"), ("timeBand", "night")],
                ("mon_morning_tue_night", "mon_morning_tue_all_day"),
            ),
            # The unpublished revision's Monday-night row never matches.
            (
                [("weekday", "1"), ("timeBand", "morning")],
                (
                    "mon_morning_tue_night",
                    "mon_all_day",
                    "mon_morning_tue_all_day",
                    "unpublished_night",
                ),
            ),
            # No schedule filter: nothing is excluded for its schedules.
            ([], D4_KEYS),
        ],
    )
    @pytest.mark.parametrize("sort", ["newest", "most_favorited"])
    def test_weekday_and_time_band_semantics(
        self,
        client: TestClient,
        params: list[tuple[str, str]],
        expected_keys: tuple[str, ...],
        sort: str,
    ) -> None:
        response = _d4_search(client, params, sort=sort)

        _assert_d4_result(response, _d4(*expected_keys))

    @pytest.mark.parametrize("band", REGULAR_BANDS)
    def test_irregular_time_band_never_matches_a_regular_band(
        self, client: TestClient, band: str
    ) -> None:
        response = _d4_search(client, [("timeBand", band)])
        ids = set(_ids(response))

        assert ids.isdisjoint(_d4("irregular_only", "mon_irregular", "no_schedule"))
        assert _d4("mon_all_day") <= ids

    def test_mixed_schedule_rows_do_not_combine_across_rows(self, client: TestClient) -> None:
        # Monday-morning + Tuesday-night, and Monday-morning + Tuesday-all_day.
        response = client.get(
            "/api/v1/circles",
            params=[("weekday", "1"), ("timeBand", "night"), ("limit", "50")],
        )
        ids = set(_ids(response))

        assert ids.isdisjoint(
            _d4("mon_morning_tue_night", "mon_morning_tue_all_day", "unpublished_night")
        )
        assert _d4("mon_all_day", "mon_night") <= ids

    def test_schedule_filters_are_and_with_other_structured_filters(
        self, client: TestClient
    ) -> None:
        unofficial = _d4_search(
            client, [("weekday", "1"), ("timeBand", "night"), ("officialStatus", "unofficial")]
        )
        official = _d4_search(
            client, [("weekday", "1"), ("timeBand", "night"), ("officialStatus", "official")]
        )

        _assert_d4_result(unofficial, _d4("mon_night"))
        _assert_d4_result(official, _d4("mon_all_day"))

    @pytest.mark.parametrize("sort", ["newest", "most_favorited"])
    def test_paginated_schedule_search_has_no_gaps_or_duplicates(
        self, client: TestClient, sort: str
    ) -> None:
        params = [("q", D4_QUERY), ("timeBand", "night"), ("sort", sort), ("limit", "2")]
        expected = _d4(
            "mon_morning_tue_night",
            "mon_all_day",
            "mon_morning_tue_all_day",
            "mon_night",
            "null_weekday_night",
        )
        collected: list[str] = []
        response = client.get("/api/v1/circles", params=params)
        while True:
            collected.extend(_ids(response))
            page = response.json()["page"]
            assert page["totalCount"] == len(expected)
            if not page["hasMore"]:
                break
            response = client.get(
                "/api/v1/circles", params=[*params, ("cursor", page["nextCursor"])]
            )

        assert len(collected) == len(set(collected))
        assert set(collected) == expected

    @pytest.mark.parametrize(
        "changed",
        [
            [("weekday", "2"), ("timeBand", "night")],
            [("weekday", "1"), ("timeBand", "evening")],
            [("weekday", "1")],
            [("timeBand", "night")],
            [("weekday", "1"), ("timeBand", "night"), ("timeBand", "all_day")],
        ],
    )
    def test_cursor_is_bound_to_the_schedule_filters(
        self, client: TestClient, changed: list[tuple[str, str]]
    ) -> None:
        first = _d4_search(client, [("weekday", "1"), ("timeBand", "night")], limit="1")
        cursor = first.json()["page"]["nextCursor"]
        assert cursor is not None

        reused = client.get(
            "/api/v1/circles",
            params=[("q", D4_QUERY), ("limit", "1"), ("cursor", cursor), *changed],
        )

        assert reused.status_code == 400
        assert reused.headers["content-type"].startswith("application/problem+json")
        assert reused.json()["code"] == "INVALID_CURSOR"
