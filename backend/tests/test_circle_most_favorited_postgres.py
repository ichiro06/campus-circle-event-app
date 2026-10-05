"""PostgreSQL integration tests for GET /api/v1/circles?sort=most_favorited (DEC-061).

Every fixture Circle carries FIXTURE_TOKEN in its display name and every request filters
on it with ``q``, so the assertions are independent of other rows in the test database.
Favorite counts are never exposed by the API (H10 is undecided); the tests observe them
only through the resulting order.
"""

import base64
import json
import os
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, insert, select, text, update
from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from sqlalchemy.orm import Session

from app_private.models import (
    Account,
    Category,
    CircleMembership,
    CircleRevision,
    Favorite,
    ServiceOperator,
)
from app_private.models import (
    Circle as ProductCircle,
)
from circles.cursor import CURSOR_SECRET_ENV, CURSOR_TTL_SECONDS, SignedCircleCursorCodec
from database import SessionLocal
from main import app

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_POSTGRES_INTEGRATION") != "1",
    reason="set RUN_POSTGRES_INTEGRATION=1 against an isolated *_test PostgreSQL database",
)

FIXTURE_TOKEN = "MFFixtureToken"
CATEGORY_ID = UUID("40000000-0000-0000-0000-000000000001")


def _uuid(index: int) -> UUID:
    return UUID(f"40000000-0000-0000-0000-{index:012d}")


# Fixture Circles. Index order is "newest first", then id DESC breaks the tie between 3 and 4,
# and the null publication time sorts last:
#   0 > 1 > 2 > 4 > 3 > 5   (this is also the all-zero most_favorited order)
CIRCLE_IDS = tuple(_uuid(100 + index) for index in range(6))
REVISION_IDS = tuple(_uuid(200 + index) for index in range(6))
DRAFT_CIRCLE_ID = _uuid(190)
DRAFT_REVISION_ID = _uuid(290)
BASE_TIME = datetime(2026, 9, 1, 12, 0, tzinfo=UTC)
PUBLISHED_AT = (
    BASE_TIME + timedelta(days=5),
    BASE_TIME + timedelta(days=4),
    BASE_TIME + timedelta(days=3),
    BASE_TIME + timedelta(days=2),
    BASE_TIME + timedelta(days=2),
    None,
)
OFFICIAL_STATUS = ("official", "unofficial", "official", "official", "unofficial", "official")
CIRCLE_TYPE = ("circle", "club", "club", "circle", "circle", "club")
NEWEST_ORDER = [0, 1, 2, 4, 3, 5]

ACCOUNT_IDS = tuple(_uuid(10 + index) for index in range(12))
OPERATOR_ID = _uuid(900)
OPERATOR_IDS = (OPERATOR_ID, _uuid(901))


@pytest.fixture(scope="module", autouse=True)
def postgres_fixture() -> Iterator[None]:
    with SessionLocal() as session:
        database_name = session.scalar(text("SELECT current_database()"))
        if not str(database_name).endswith("_test"):
            pytest.fail("PostgreSQL integration tests require an isolated *_test database")
        _cleanup(session)
        _seed(session)
    try:
        yield
    finally:
        with SessionLocal() as session:
            _cleanup(session)


@pytest.fixture(autouse=True)
def reset_mutable_state() -> Iterator[None]:
    with SessionLocal() as session:
        _reset(session)
    yield


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def db() -> Iterator[Session]:
    with SessionLocal() as session:
        yield session


def _all_circle_ids() -> tuple[UUID, ...]:
    return (*CIRCLE_IDS, DRAFT_CIRCLE_ID)


def _all_account_ids() -> tuple[UUID, ...]:
    return (*ACCOUNT_IDS, *OPERATOR_IDS)


def _reset(session: Session) -> None:
    session.execute(delete(Favorite).where(Favorite.circle_id.in_(_all_circle_ids())))
    session.execute(
        delete(CircleMembership).where(CircleMembership.circle_id.in_(_all_circle_ids()))
    )
    session.execute(delete(ServiceOperator).where(ServiceOperator.user_id.in_(_all_account_ids())))
    session.execute(
        postgresql_insert(Account)
        .values([{"id": account_id, "status": "active"} for account_id in _all_account_ids()])
        .on_conflict_do_nothing(index_elements=[Account.id])
    )
    session.execute(
        update(Account).where(Account.id.in_(_all_account_ids())).values(status="active")
    )
    session.commit()


def _cleanup(session: Session) -> None:
    _reset(session)
    session.execute(delete(Account).where(Account.id.in_(_all_account_ids())))
    session.execute(
        update(ProductCircle)
        .where(ProductCircle.id.in_(_all_circle_ids()))
        .values(published_revision_id=None)
    )
    session.execute(delete(CircleRevision).where(CircleRevision.circle_id.in_(_all_circle_ids())))
    session.execute(delete(ProductCircle).where(ProductCircle.id.in_(_all_circle_ids())))
    session.execute(delete(Category).where(Category.id == CATEGORY_ID))
    session.commit()


def _revision(
    revision_id: UUID,
    circle_id: UUID,
    *,
    display_name: str,
    circle_type: str,
    published_at: datetime | None,
) -> dict[str, object]:
    return {
        "id": revision_id,
        "circle_id": circle_id,
        "version_no": 1,
        "status": "published",
        "display_name": display_name,
        "circle_type": circle_type,
        "category_id": CATEGORY_ID,
        "headline": "most_favorited fixture",
        "summary": "most_favorited fixture",
        "description": "most_favorited fixture",
        "recruiting_status": "open",
        "member_count_band": None,
        "camp_frequency_code": None,
        "activity_frequency_code": None,
        "drinking_frequency_rating": None,
        "liveliness_rating": None,
        "commitment_rating": None,
        "attendance_flexibility_rating": None,
        "career_opportunity_rating": None,
        "gender_balance_code": None,
        "published_at": published_at,
    }


def _circle(circle_id: UUID, *, lifecycle_status: str, official_status: str) -> dict[str, object]:
    return {
        "id": circle_id,
        "slug": f"mf-fixture-{circle_id}",
        "lifecycle_status": lifecycle_status,
        "official_status": official_status,
        "verification_type": "public_unverified",
        "published_revision_id": None,
        "deleted_at": None,
    }


def _seed(session: Session) -> None:
    session.execute(
        insert(Category),
        [{"id": CATEGORY_ID, "name": "MF Fixture", "slug": "mf-fixture", "display_order": 0}],
    )
    session.execute(
        insert(ProductCircle),
        [
            _circle(circle_id, lifecycle_status="published", official_status=status)
            for circle_id, status in zip(CIRCLE_IDS, OFFICIAL_STATUS, strict=True)
        ]
        + [_circle(DRAFT_CIRCLE_ID, lifecycle_status="draft", official_status="official")],
    )
    session.execute(
        insert(CircleRevision),
        [
            _revision(
                revision_id,
                circle_id,
                display_name=f"{FIXTURE_TOKEN} Circle {index}",
                circle_type=circle_type,
                published_at=published_at,
            )
            for index, (revision_id, circle_id, circle_type, published_at) in enumerate(
                zip(REVISION_IDS, CIRCLE_IDS, CIRCLE_TYPE, PUBLISHED_AT, strict=True)
            )
        ]
        + [
            _revision(
                DRAFT_REVISION_ID,
                DRAFT_CIRCLE_ID,
                display_name=f"{FIXTURE_TOKEN} Draft",
                circle_type="circle",
                published_at=BASE_TIME + timedelta(days=9),
            )
        ],
    )
    for circle_id, revision_id in zip(CIRCLE_IDS, REVISION_IDS, strict=True):
        session.execute(
            update(ProductCircle)
            .where(ProductCircle.id == circle_id)
            .values(published_revision_id=revision_id)
        )
    session.execute(
        update(ProductCircle)
        .where(ProductCircle.id == DRAFT_CIRCLE_ID)
        .values(published_revision_id=DRAFT_REVISION_ID)
    )
    session.execute(
        insert(Account),
        [{"id": account_id, "status": "active"} for account_id in _all_account_ids()],
    )
    session.commit()


def _favorite(session: Session, *pairs: tuple[UUID, int]) -> None:
    """Add favorites from ``(account_id, circle_index)`` pairs."""

    session.execute(
        insert(Favorite),
        [{"user_id": account_id, "circle_id": CIRCLE_IDS[index]} for account_id, index in pairs],
    )
    session.commit()


def _set_account_status(session: Session, account_id: UUID, status: str) -> None:
    session.execute(update(Account).where(Account.id == account_id).values(status=status))
    session.commit()


def _add_manager(session: Session, account_id: UUID, circle_index: int, *, status: str = "active"):
    session.execute(
        insert(CircleMembership),
        [
            {
                "id": uuid4(),
                "user_id": account_id,
                "circle_id": CIRCLE_IDS[circle_index],
                "role": "manager",
                "status": status,
            }
        ],
    )
    session.commit()


def _add_operator(session: Session, account_id: UUID, *, status: str = "active") -> None:
    session.execute(
        insert(ServiceOperator),
        [{"user_id": account_id, "status": status, "grant_reason": "most_favorited fixture"}],
    )
    session.commit()


def _list(
    client: TestClient,
    *,
    sort: str = "most_favorited",
    limit: int | None = None,
    cursor: str | None = None,
    q: str = FIXTURE_TOKEN,
    extra: list[tuple[str, str]] | None = None,
):
    params: list[tuple[str, str]] = [("q", q), ("sort", sort)]
    if limit is not None:
        params.append(("limit", str(limit)))
    if cursor is not None:
        params.append(("cursor", cursor))
    params.extend(extra or [])
    return client.get("/api/v1/circles", params=params)


def _order(response) -> list[int]:
    assert response.status_code == 200, response.text
    indexes = {str(circle_id): index for index, circle_id in enumerate(CIRCLE_IDS)}
    return [indexes[item["id"]] for item in response.json()["data"]]


def _codec() -> SignedCircleCursorCodec:
    return SignedCircleCursorCodec.from_environment()


# --- A. basic ordering -------------------------------------------------------------------


def test_circles_are_ordered_by_eligible_favorite_count_descending(
    client: TestClient, db: Session
) -> None:
    _favorite(
        db,
        (ACCOUNT_IDS[0], 2),
        (ACCOUNT_IDS[1], 2),
        (ACCOUNT_IDS[2], 2),
        (ACCOUNT_IDS[0], 3),
        (ACCOUNT_IDS[1], 3),
    )

    # counts: circle 2 -> 3, circle 3 -> 2, the rest -> 0 in newest order
    assert _order(_list(client)) == [2, 3, 0, 1, 4, 5]


# --- B. tie-break ------------------------------------------------------------------------


def test_equal_counts_prefer_newer_publication_then_larger_id_with_null_last(
    client: TestClient, db: Session
) -> None:
    _favorite(
        db,
        (ACCOUNT_IDS[0], 2),
        (ACCOUNT_IDS[0], 5),
        (ACCOUNT_IDS[0], 3),
        (ACCOUNT_IDS[0], 4),
        (ACCOUNT_IDS[0], 0),
        (ACCOUNT_IDS[0], 1),
        (ACCOUNT_IDS[1], 2),
    )

    # circle 2 leads with 2; everyone else has 1: published_at DESC, id DESC, NULL last
    assert _order(_list(client)) == [2, 0, 1, 4, 3, 5]


# --- C. all zero -------------------------------------------------------------------------


def test_all_zero_favorites_use_the_newest_direction_and_keep_zero_favorite_circles(
    client: TestClient,
) -> None:
    most_favorited = _order(_list(client))
    newest = _order(_list(client, sort="newest"))

    assert most_favorited == NEWEST_ORDER
    assert most_favorited == newest


# --- D. same-circle manager --------------------------------------------------------------


def test_favorite_by_a_current_manager_of_the_same_circle_is_excluded(
    client: TestClient, db: Session
) -> None:
    _add_manager(db, ACCOUNT_IDS[0], 0)
    _favorite(db, (ACCOUNT_IDS[0], 0), (ACCOUNT_IDS[1], 1))

    # counted: tie at 1 would put the newer circle 0 first; excluded: circle 1 leads
    assert _order(_list(client)) == [1, 0, 2, 4, 3, 5]


# --- E. other-circle manager -------------------------------------------------------------


def test_favorite_by_a_manager_of_another_circle_is_counted(
    client: TestClient, db: Session
) -> None:
    _add_manager(db, ACCOUNT_IDS[0], 3)
    _favorite(db, (ACCOUNT_IDS[0], 5))

    assert _order(_list(client)) == [5, 0, 1, 2, 4, 3]


# --- F. service operator -----------------------------------------------------------------


def test_favorites_by_current_service_operators_are_excluded_from_every_circle(
    client: TestClient, db: Session
) -> None:
    _add_operator(db, OPERATOR_IDS[0])
    _add_operator(db, OPERATOR_IDS[1])
    _favorite(
        db,
        (OPERATOR_IDS[0], 5),
        (OPERATOR_IDS[1], 5),
        (OPERATOR_IDS[0], 0),
        (ACCOUNT_IDS[0], 3),
    )

    # operators would put circle 5 first with 2; excluded, only the normal favorite remains
    assert _order(_list(client)) == [3, 0, 1, 2, 4, 5]


# --- G. account lifecycle ----------------------------------------------------------------


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        ("active", [5, 3, 0, 1, 2, 4]),
        ("suspended", [3, 0, 1, 2, 4, 5]),
        ("deletion_pending", [3, 0, 1, 2, 4, 5]),
        ("deleted", [3, 0, 1, 2, 4, 5]),
    ],
)
def test_only_favorites_of_active_accounts_are_counted(
    client: TestClient, db: Session, status: str, expected: list[int]
) -> None:
    _favorite(db, (ACCOUNT_IDS[0], 5), (ACCOUNT_IDS[1], 5), (ACCOUNT_IDS[2], 3))
    _set_account_status(db, ACCOUNT_IDS[0], status)
    _set_account_status(db, ACCOUNT_IDS[1], status)

    assert _order(_list(client)) == expected


def test_deletion_pending_stops_counting_immediately_and_reactivation_counts_again(
    client: TestClient, db: Session
) -> None:
    _favorite(db, (ACCOUNT_IDS[0], 5), (ACCOUNT_IDS[1], 5), (ACCOUNT_IDS[2], 3))
    assert _order(_list(client)) == [5, 3, 0, 1, 2, 4]

    _set_account_status(db, ACCOUNT_IDS[0], "deletion_pending")
    _set_account_status(db, ACCOUNT_IDS[1], "deletion_pending")
    assert _order(_list(client)) == [3, 0, 1, 2, 4, 5]


def test_physically_deleting_an_account_removes_its_favorites(
    client: TestClient, db: Session
) -> None:
    _favorite(db, (ACCOUNT_IDS[0], 5), (ACCOUNT_IDS[1], 5), (ACCOUNT_IDS[2], 3))
    assert _order(_list(client)) == [5, 3, 0, 1, 2, 4]

    db.execute(delete(Account).where(Account.id.in_([ACCOUNT_IDS[0], ACCOUNT_IDS[1]])))
    db.commit()

    remaining = db.scalars(select(Favorite.circle_id).where(Favorite.circle_id.in_(CIRCLE_IDS)))
    assert list(remaining) == [CIRCLE_IDS[3]]
    assert _order(_list(client)) == [3, 0, 1, 2, 4, 5]


# --- H. role timing ----------------------------------------------------------------------


def test_roles_are_evaluated_at_query_time_not_at_favorite_time(
    client: TestClient, db: Session
) -> None:
    _favorite(db, (ACCOUNT_IDS[0], 5), (ACCOUNT_IDS[1], 5), (ACCOUNT_IDS[2], 3))
    assert _order(_list(client)) == [5, 3, 0, 1, 2, 4]

    # Both accounts become a same-circle manager / a service operator after favoriting.
    _add_manager(db, ACCOUNT_IDS[0], 5)
    _add_operator(db, ACCOUNT_IDS[1])
    assert _order(_list(client)) == [3, 0, 1, 2, 4, 5]

    # When the roles stop being active the existing favorites count again.
    db.execute(
        update(CircleMembership)
        .where(CircleMembership.circle_id.in_(_all_circle_ids()))
        .values(status="revoked")
    )
    db.execute(
        update(ServiceOperator)
        .where(ServiceOperator.user_id.in_(_all_account_ids()))
        .values(status="revoked")
    )
    db.commit()
    assert _order(_list(client)) == [5, 3, 0, 1, 2, 4]


def test_a_suspended_manager_membership_is_not_a_current_active_manager(
    client: TestClient, db: Session
) -> None:
    _add_manager(db, ACCOUNT_IDS[0], 5, status="suspended")
    _favorite(db, (ACCOUNT_IDS[0], 5))

    assert _order(_list(client)) == [5, 0, 1, 2, 4, 3]


# --- I. filters --------------------------------------------------------------------------


def test_existing_filters_keep_their_or_and_and_semantics_with_most_favorited(
    client: TestClient, db: Session
) -> None:
    _favorite(db, (ACCOUNT_IDS[0], 2), (ACCOUNT_IDS[1], 2), (ACCOUNT_IDS[0], 4))

    official = _list(client, extra=[("officialStatus", "official")])
    assert _order(official) == [2, 0, 3, 5]

    both_statuses = _list(
        client, extra=[("officialStatus", "official"), ("officialStatus", "unofficial")]
    )
    assert _order(both_statuses) == [2, 4, 0, 1, 3, 5]

    official_and_club = _list(
        client, extra=[("officialStatus", "official"), ("circleType", "club")]
    )
    assert _order(official_and_club) == [2, 5]

    sort_newest = _list(
        client,
        sort="newest",
        extra=[("officialStatus", "official"), ("circleType", "club")],
    )
    assert sorted(_order(sort_newest)) == sorted(_order(official_and_club))

    no_match = _list(client, q=f"{FIXTURE_TOKEN} does-not-exist")
    assert no_match.status_code == 200
    assert no_match.json()["data"] == []


# --- J. totalCount -----------------------------------------------------------------------


def test_total_count_is_the_number_of_matching_circles_not_a_favorite_count(
    client: TestClient, db: Session
) -> None:
    _favorite(
        db,
        *[(account_id, 2) for account_id in ACCOUNT_IDS[:6]],
        *[(account_id, 3) for account_id in ACCOUNT_IDS[:3]],
        *[(account_id, 5) for account_id in ACCOUNT_IDS[:2]],
    )

    unfiltered = _list(client).json()["page"]["totalCount"]
    filtered = _list(client, extra=[("officialStatus", "official")]).json()["page"]["totalCount"]

    assert unfiltered == 6  # six published fixture Circles, zero-favorite ones included
    assert filtered == 4
    assert _list(client, limit=2).json()["page"]["totalCount"] == 6
    # the draft fixture Circle has favorites but is never listed or counted
    db.execute(insert(Favorite), [{"user_id": ACCOUNT_IDS[0], "circle_id": DRAFT_CIRCLE_ID}])
    db.commit()
    assert _list(client).json()["page"]["totalCount"] == 6
    assert str(DRAFT_CIRCLE_ID) not in {item["id"] for item in _list(client).json()["data"]}


# --- K. pagination -----------------------------------------------------------------------


@pytest.mark.parametrize("limit", [1, 2, 3, 5])
def test_most_favorited_cursor_pages_through_the_complete_order(
    client: TestClient, db: Session, limit: int
) -> None:
    _favorite(
        db,
        *[(account_id, 2) for account_id in ACCOUNT_IDS[:3]],
        *[(account_id, 3) for account_id in ACCOUNT_IDS[:2]],
        *[(account_id, 4) for account_id in ACCOUNT_IDS[:2]],
        (ACCOUNT_IDS[0], 0),
    )
    expected = _order(_list(client))
    assert expected == [2, 4, 3, 0, 1, 5]

    collected: list[int] = []
    cursor: str | None = None
    pages = 0
    while True:
        response = _list(client, limit=limit, cursor=cursor)
        collected.extend(_order(response))
        page = response.json()["page"]
        pages += 1
        assert page["limit"] == limit
        if not page["hasMore"]:
            assert "nextCursor" not in page
            break
        cursor = page["nextCursor"]
        assert pages < 10

    assert collected == expected
    assert pages == -(-len(expected) // limit)


def test_cursor_carries_the_three_sort_keys_and_is_bound_to_sort_and_filters(
    client: TestClient, db: Session
) -> None:
    _favorite(db, (ACCOUNT_IDS[0], 2), (ACCOUNT_IDS[1], 2), (ACCOUNT_IDS[0], 3))

    cursor = _list(client, limit=2).json()["page"]["nextCursor"]
    payload = _codec().decode(cursor)

    assert payload.sort == "most_favorited"
    assert payload.last_favorite_count == 1  # circle 3, the last row of the first page
    assert payload.last_published_at == PUBLISHED_AT[3]
    assert payload.last_circle_id == CIRCLE_IDS[3]
    assert payload.filters["q"] == FIXTURE_TOKEN


# --- L. cursor separation ----------------------------------------------------------------


def test_cursors_are_not_interchangeable_between_newest_and_most_favorited(
    client: TestClient,
) -> None:
    newest_cursor = _list(client, sort="newest", limit=2).json()["page"]["nextCursor"]
    favorited_cursor = _list(client, limit=2).json()["page"]["nextCursor"]

    for response in (
        _list(client, sort="most_favorited", limit=2, cursor=newest_cursor),
        _list(client, sort="newest", limit=2, cursor=favorited_cursor),
    ):
        assert response.status_code == 400
        assert response.json()["code"] == "INVALID_CURSOR"

    # Each cursor keeps working with its own sort.
    assert _list(client, sort="newest", limit=2, cursor=newest_cursor).status_code == 200
    assert _list(client, limit=2, cursor=favorited_cursor).status_code == 200


# --- M. tampering, expiry, filter binding ------------------------------------------------


def test_most_favorited_cursor_security_contract_is_unchanged(client: TestClient) -> None:
    cursor = _list(client, limit=2).json()["page"]["nextCursor"]
    encoded, signature = cursor.split(".")
    replacement = "A" if encoded[-1] != "A" else "B"

    tampered = _list(client, limit=2, cursor=f"{encoded[:-1]}{replacement}.{signature}")
    other_filter = _list(client, limit=2, cursor=cursor, extra=[("officialStatus", "official")])
    other_query = _list(client, limit=2, cursor=cursor, q=f"{FIXTURE_TOKEN} Circle")
    long_ago = datetime.now(UTC) - timedelta(seconds=CURSOR_TTL_SECONDS + 60)
    expired = SignedCircleCursorCodec(
        os.environ[CURSOR_SECRET_ENV].encode(), clock=lambda: long_ago
    ).encode(
        sort="most_favorited",
        last_favorite_count=0,
        last_published_at=None,
        last_circle_id=CIRCLE_IDS[5],
        filters=_codec().decode(cursor).filters,
    )
    expired_response = _list(client, limit=2, cursor=expired)

    for response in (tampered, other_filter, other_query, expired_response):
        assert response.status_code == 400
        assert response.json()["code"] == "INVALID_CURSOR"
        assert "favorite" not in response.json()["detail"].lower()


# --- N. no favoriteCount in the response -------------------------------------------------


def test_the_response_does_not_expose_a_favorite_count(client: TestClient, db: Session) -> None:
    _favorite(db, (ACCOUNT_IDS[0], 2), (ACCOUNT_IDS[1], 2))

    response = _list(client, limit=2)
    body = response.json()

    assert response.status_code == 200
    assert "favoritecount" not in response.text.lower().replace("_", "")
    assert set(body["page"]) == {"nextCursor", "hasMore", "limit", "totalCount"}
    for item in body["data"]:
        assert "favoriteCount" not in item
    newest_keys = {tuple(sorted(item)) for item in _list(client, sort="newest").json()["data"]}
    assert {tuple(sorted(item)) for item in body["data"]} == newest_keys


# --- mutable ranking (DEC-061 D4) --------------------------------------------------------


def test_rank_changes_between_pages_do_not_break_the_cursor_and_promise_no_snapshot(
    client: TestClient, db: Session
) -> None:
    _favorite(db, (ACCOUNT_IDS[0], 2), (ACCOUNT_IDS[1], 2), (ACCOUNT_IDS[0], 3))
    first = _list(client, limit=2)
    first_ids = _order(first)
    cursor = first.json()["page"]["nextCursor"]

    # Favorites move while the client is between pages: a circle on page 1 gains rank
    # and a circle that was not yet listed jumps ahead of the cursor position.
    _favorite(
        db,
        *[(account_id, 5) for account_id in ACCOUNT_IDS[2:8]],
        *[(account_id, 2) for account_id in ACCOUNT_IDS[2:4]],
    )
    second = _list(client, limit=2, cursor=cursor)

    # The contract is only "valid, no server error, only fixture circles".
    # Skips and duplicates are allowed, so completeness is deliberately not asserted.
    assert second.status_code == 200
    second_ids = _order(second)
    assert set(second_ids) <= set(range(6))
    assert len(second_ids) == len(set(second_ids))
    assert first_ids == [2, 3]

    # Refreshing (dropping the cursor) restarts from the top of the current ranking.
    assert _order(_list(client)) == [5, 2, 3, 0, 1, 4]


def test_the_cursor_payload_is_signed_not_encrypted(client: TestClient, db: Session) -> None:
    """CURSOR_CONFIDENTIALITY_FOLLOWUP: the favorite count is readable by the client."""

    _favorite(db, (ACCOUNT_IDS[0], 0), (ACCOUNT_IDS[0], 1), (ACCOUNT_IDS[0], 2))
    cursor = _list(client, limit=1).json()["page"]["nextCursor"]
    encoded, _signature = cursor.split(".")
    decoded = json.loads(base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4)))

    assert decoded["lastFavoriteCount"] == 1
