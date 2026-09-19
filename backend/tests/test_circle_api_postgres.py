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

PUBLISHED_AT = datetime(2026, 9, 18, 12, 0, tzinfo=UTC)
OLDER_PUBLISHED_AT = datetime(2026, 9, 17, 12, 0, tzinfo=UTC)


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
    all_circle_ids = (*CIRCLE_IDS, TRANSIENT_CIRCLE_ID)
    all_revision_ids = (*REVISION_IDS, TRANSIENT_REVISION_ID)
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
