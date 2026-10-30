import os
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, func, insert, select, text, update
from sqlalchemy.orm import Session

from app_private.models import (
    Category,
    CircleRevision,
    CircleRevisionTag,
    Tag,
)
from app_private.models import (
    Circle as ProductCircle,
)
from app_private.seed_tags import (
    INITIAL_TAGS,
    SeedConflictError,
    plan_initial_tags,
    seed_initial_tags,
)
from app_private.seed_tags import (
    main as seed_main,
)
from circles.cursor import CURSOR_SECRET_ENV, SignedCircleCursorCodec
from database import SessionLocal
from main import app

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_POSTGRES_INTEGRATION") != "1",
    reason="set RUN_POSTGRES_INTEGRATION=1 against an isolated *_test PostgreSQL database",
)

CATEGORY_ID = UUID("40000000-0000-0000-0000-000000000001")
ACTIVE_TAG_ID = UUID("40000000-0000-0000-0000-000000000011")
INACTIVE_TAG_ID = UUID("40000000-0000-0000-0000-000000000012")
CIRCLE_IDS = (
    UUID("40000000-0000-0000-0000-000000000101"),
    UUID("40000000-0000-0000-0000-000000000102"),
)
REVISION_IDS = (
    UUID("40000000-0000-0000-0000-000000000201"),
    UUID("40000000-0000-0000-0000-000000000202"),
    UUID("40000000-0000-0000-0000-000000000203"),
)
ORDERED_TAG_IDS = tuple(UUID(f"40000000-0000-0000-0000-{index:012d}") for index in range(21, 29))
CONFLICT_TAG_ID = UUID("40000000-0000-0000-0000-000000000031")
OWNED_TAG_IDS = (
    ACTIVE_TAG_ID,
    INACTIVE_TAG_ID,
    *ORDERED_TAG_IDS,
    CONFLICT_TAG_ID,
    *(tag.id for tag in INITIAL_TAGS),
)
PUBLISHED_AT = datetime(2026, 10, 1, 12, 0, tzinfo=UTC)
INACTIVE_NAME = "非アクティブ検証タグ"
ACTIVE_NAME = "アクティブ検証タグ"


def _tag(tag_id: UUID, name: str, slug: str, display_order: int, *, is_active: bool = True) -> dict:
    return {
        "id": tag_id,
        "name": name,
        "slug": slug,
        "display_order": display_order,
        "is_active": is_active,
    }


def _cleanup(session: Session) -> None:
    session.execute(
        update(ProductCircle)
        .where(ProductCircle.id.in_(CIRCLE_IDS))
        .values(published_revision_id=None)
    )
    session.execute(
        delete(CircleRevisionTag).where(CircleRevisionTag.revision_id.in_(REVISION_IDS))
    )
    session.execute(delete(CircleRevision).where(CircleRevision.id.in_(REVISION_IDS)))
    session.execute(delete(ProductCircle).where(ProductCircle.id.in_(CIRCLE_IDS)))
    session.execute(delete(Tag).where(Tag.id.in_(OWNED_TAG_IDS)))
    session.execute(delete(Category).where(Category.id == CATEGORY_ID))
    session.commit()


@pytest.fixture(autouse=True)
def isolated_tags() -> Iterator[None]:
    """Give every test an empty tag master and remove everything it created afterwards."""

    with SessionLocal() as session:
        database_name = session.scalar(text("SELECT current_database()"))
        if not str(database_name).endswith("_test"):
            pytest.fail("PostgreSQL integration tests require an isolated *_test database")
        _cleanup(session)
        foreign = session.scalar(select(func.count()).select_from(Tag))
        if foreign:
            pytest.fail(f"{foreign} tag(s) not owned by this module exist in the test database")
    yield
    with SessionLocal() as session:
        _cleanup(session)


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app, raise_server_exceptions=False)


def _insert_tags(rows: list[dict]) -> None:
    with SessionLocal() as session:
        session.execute(insert(Tag), rows)
        session.commit()


def _names(response) -> list[str]:
    assert response.status_code == 200, response.text
    return [item["name"] for item in response.json()["data"]]


def _seed() -> None:
    with SessionLocal() as session:
        seed_initial_tags(session, apply=True)


def _tag_rows() -> list[tuple]:
    with SessionLocal() as session:
        return [
            tuple(row)
            for row in session.execute(
                select(Tag.id, Tag.name, Tag.slug, Tag.display_order, Tag.is_active).order_by(
                    Tag.display_order, Tag.id
                )
            )
        ]


# ---- Public catalog ---------------------------------------------------------------------


def test_empty_catalog_is_a_normal_collection(client: TestClient) -> None:
    response = client.get("/api/v1/tags")
    body = response.json()

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert body["data"] == []
    assert body["page"] == {"hasMore": False, "limit": 20}
    assert UUID(body["meta"]["requestId"])
    assert set(body) == {"data", "page", "meta"}


def test_only_active_tags_are_listed_with_the_exact_public_shape(client: TestClient) -> None:
    _insert_tags(
        [
            _tag(ACTIVE_TAG_ID, ACTIVE_NAME, "active-fixture", 1),
            _tag(INACTIVE_TAG_ID, INACTIVE_NAME, "inactive-fixture", 0, is_active=False),
        ]
    )

    response = client.get("/api/v1/tags")
    body = response.json()

    assert _names(response) == [ACTIVE_NAME]
    assert body["data"] == [
        {"id": str(ACTIVE_TAG_ID), "name": ACTIVE_NAME, "slug": "active-fixture"}
    ]
    assert "totalCount" not in body["page"]
    assert (
        response.json()["meta"]["requestId"]
        != client.get("/api/v1/tags").json()["meta"]["requestId"]
    )


def test_all_inactive_catalog_is_empty(client: TestClient) -> None:
    _insert_tags([_tag(INACTIVE_TAG_ID, INACTIVE_NAME, "inactive-fixture", 0, is_active=False)])

    response = client.get("/api/v1/tags")

    assert response.status_code == 200
    assert response.json()["data"] == []
    assert response.json()["page"] == {"hasMore": False, "limit": 20}


def test_order_is_display_order_then_id_regardless_of_insert_order(client: TestClient) -> None:
    # Two tags share display_order 5; the lower UUID must come first even though the
    # higher UUID is inserted (and therefore stored) first.
    _insert_tags(
        [
            _tag(ORDERED_TAG_IDS[0], "順序C", "order-c", 9),
            _tag(ORDERED_TAG_IDS[2], "順序B2", "order-b2", 5),
            _tag(ORDERED_TAG_IDS[1], "順序B1", "order-b1", 5),
            _tag(ORDERED_TAG_IDS[3], "順序A", "order-a", 0),
        ]
    )

    first = client.get("/api/v1/tags")
    second = client.get("/api/v1/tags")

    assert _names(first) == ["順序A", "順序B1", "順序B2", "順序C"]
    assert first.json()["data"] == second.json()["data"]


def test_pagination_walks_every_tag_once_in_order(client: TestClient) -> None:
    # display_order values repeat in pairs, and rows are stored in descending ID order, so a
    # page boundary falls inside a tie and only the ID tie-breaker keeps the walk exact.
    _insert_tags(
        [
            _tag(tag_id, f"ページ{index}", f"page-{index}", index // 2)
            for index, tag_id in reversed(list(enumerate(ORDERED_TAG_IDS)))
        ]
    )
    expected = [f"ページ{index}" for index in range(len(ORDERED_TAG_IDS))]

    seen: list[str] = []
    cursor = None
    pages = 0
    while True:
        params = {"limit": 3} | ({"cursor": cursor} if cursor else {})
        response = client.get("/api/v1/tags", params=params)
        assert response.status_code == 200, response.text
        body = response.json()
        seen += [item["name"] for item in body["data"]]
        pages += 1
        assert body["page"]["limit"] == 3
        if not body["page"]["hasMore"]:
            assert "nextCursor" not in body["page"]
            break
        assert body["page"]["nextCursor"]
        assert len(body["data"]) == 3
        cursor = body["page"]["nextCursor"]

    assert seen == expected
    assert pages == 3


def test_pagination_skips_a_tag_deactivated_between_pages(client: TestClient) -> None:
    _insert_tags(
        [
            _tag(tag_id, f"移動{index}", f"move-{index}", index)
            for index, tag_id in enumerate(ORDERED_TAG_IDS[:4])
        ]
    )
    first = client.get("/api/v1/tags", params={"limit": 2}).json()
    with SessionLocal() as session:
        session.execute(update(Tag).where(Tag.id == ORDERED_TAG_IDS[2]).values(is_active=False))
        session.commit()

    second = client.get(
        "/api/v1/tags", params={"limit": 2, "cursor": first["page"]["nextCursor"]}
    ).json()

    assert [item["name"] for item in first["data"]] == ["移動0", "移動1"]
    assert [item["name"] for item in second["data"]] == ["移動3"]
    assert second["page"] == {"hasMore": False, "limit": 2}


@pytest.mark.parametrize(
    "params",
    [
        {"limit": 0},
        {"limit": 51},
        {"limit": "many"},
        {"cursor": ""},
        {"unknown": "1"},
        {"q": "初心者"},
        {"isActive": "false"},
    ],
)
def test_query_validation_is_a_422_problem(client: TestClient, params: dict) -> None:
    response = client.get("/api/v1/tags", params=params)
    body = response.json()

    assert response.status_code == 422
    assert response.headers["content-type"].startswith("application/problem+json")
    assert body["code"] == "VALIDATION_ERROR"
    assert body["instance"] == "/api/v1/tags"
    assert UUID(body["requestId"])


def test_limit_boundaries_are_accepted(client: TestClient) -> None:
    assert client.get("/api/v1/tags", params={"limit": 1}).status_code == 200
    assert client.get("/api/v1/tags", params={"limit": 50}).status_code == 200


def test_invalid_and_foreign_cursors_are_400_problems(client: TestClient) -> None:
    _insert_tags(
        [
            _tag(tag_id, f"検証{index}", f"cursor-{index}", index)
            for index, tag_id in enumerate(ORDERED_TAG_IDS[:3])
        ]
    )
    cursor = client.get("/api/v1/tags", params={"limit": 1}).json()["page"]["nextCursor"]
    circle_cursor = SignedCircleCursorCodec.from_environment().encode(
        last_published_at=PUBLISHED_AT,
        last_circle_id=CIRCLE_IDS[0],
        filters={"q": None},
    )
    tampered = cursor[:-2] + ("AA" if not cursor.endswith("AA") else "BB")

    for bad in ("not-a-cursor", tampered, circle_cursor):
        response = client.get("/api/v1/tags", params={"cursor": bad})
        assert response.status_code == 400
        assert response.headers["content-type"].startswith("application/problem+json")
        assert response.json()["code"] == "INVALID_CURSOR"
        assert bad not in response.text

    # A tag cursor is not a valid Circle cursor either.
    assert client.get("/api/v1/circles", params={"cursor": cursor}).status_code == 400


def test_public_read_needs_no_authentication_and_ignores_credentials(client: TestClient) -> None:
    _insert_tags([_tag(ACTIVE_TAG_ID, ACTIVE_NAME, "active-fixture", 1)])

    anonymous = client.get("/api/v1/tags")
    with_header = client.get("/api/v1/tags", headers={"Authorization": "Bearer not-checked"})

    assert anonymous.status_code == with_header.status_code == 200
    assert anonymous.json()["data"] == with_header.json()["data"]


def test_first_page_works_without_the_cursor_secret(monkeypatch) -> None:
    _insert_tags([_tag(ACTIVE_TAG_ID, ACTIVE_NAME, "active-fixture", 1)])
    monkeypatch.delenv(CURSOR_SECRET_ENV, raising=False)

    with TestClient(app, raise_server_exceptions=False) as secretless_client:
        single_page = secretless_client.get("/api/v1/tags")
        with_cursor = secretless_client.get("/api/v1/tags", params={"cursor": "anything"})

    assert single_page.status_code == 200
    assert _names(single_page) == [ACTIVE_NAME]
    assert with_cursor.status_code == 500
    assert CURSOR_SECRET_ENV not in with_cursor.text


# ---- Initial seed -----------------------------------------------------------------------


def test_seed_creates_exactly_the_seven_initial_tags_and_the_api_lists_them(
    client: TestClient,
) -> None:
    _seed()

    response = client.get("/api/v1/tags")

    assert _names(response) == [
        "初心者歓迎",
        "留学生歓迎",
        "兼サーOK",
        "途中入部歓迎",
        "友達作り",
        "少人数",
        "大会あり",
    ]
    assert [(item["id"], item["slug"]) for item in response.json()["data"]] == [
        (str(tag.id), tag.slug) for tag in INITIAL_TAGS
    ]
    assert _tag_rows() == [
        (tag.id, tag.name, tag.slug, tag.display_order, True) for tag in INITIAL_TAGS
    ]
    assert response.json()["page"] == {"hasMore": False, "limit": 20}


def test_seed_is_idempotent() -> None:
    _seed()
    before = _tag_rows()

    with SessionLocal() as session:
        plan = seed_initial_tags(session, apply=True)

    assert plan.to_insert == ()
    assert len(plan.unchanged) == 7
    assert _tag_rows() == before
    assert len(before) == 7


def test_dry_run_reports_the_plan_and_writes_nothing() -> None:
    with SessionLocal() as session:
        plan = seed_initial_tags(session, apply=False)

    assert plan.to_insert == INITIAL_TAGS
    assert plan.unchanged == ()
    assert _tag_rows() == []


def test_seed_only_adds_the_missing_tags_and_leaves_others_alone() -> None:
    # An unrelated operator-managed tag and one initial tag already exist.
    _insert_tags(
        [
            _tag(ACTIVE_TAG_ID, ACTIVE_NAME, "active-fixture", 40),
            _tag(
                INITIAL_TAGS[1].id,
                INITIAL_TAGS[1].name,
                INITIAL_TAGS[1].slug,
                INITIAL_TAGS[1].display_order,
            ),
        ]
    )
    before = {row[0]: row for row in _tag_rows()}

    with SessionLocal() as session:
        plan = seed_initial_tags(session, apply=True)

    after = {row[0]: row for row in _tag_rows()}
    assert len(plan.to_insert) == 6
    assert plan.unchanged == (INITIAL_TAGS[1],)
    assert len(after) == 8
    for tag_id, row in before.items():
        assert after[tag_id] == row


def test_seed_never_reactivates_or_reorders_an_existing_tag(client: TestClient) -> None:
    _seed()
    with SessionLocal() as session:
        session.execute(
            update(Tag)
            .where(Tag.id == INITIAL_TAGS[0].id)
            .values(is_active=False, display_order=99)
        )
        session.commit()
    before = _tag_rows()

    _seed()

    assert _tag_rows() == before
    assert "初心者歓迎" not in _names(client.get("/api/v1/tags"))
    assert len(_names(client.get("/api/v1/tags"))) == 6


@pytest.mark.parametrize(
    "existing",
    [
        # same name, different ID and slug
        lambda: _tag(CONFLICT_TAG_ID, INITIAL_TAGS[5].name, "other-slug", 3),
        # same slug, different ID and name
        lambda: _tag(CONFLICT_TAG_ID, "別の名前", INITIAL_TAGS[5].slug, 3),
        # same ID, different name and slug
        lambda: _tag(INITIAL_TAGS[5].id, "別の名前", "other-slug", 3),
        # same ID and name, different slug
        lambda: _tag(INITIAL_TAGS[5].id, INITIAL_TAGS[5].name, "other-slug", 3),
        # same ID and slug, different name
        lambda: _tag(INITIAL_TAGS[5].id, "別の名前", INITIAL_TAGS[5].slug, 3),
        # name and slug of the same tag, different ID
        lambda: _tag(CONFLICT_TAG_ID, INITIAL_TAGS[5].name, INITIAL_TAGS[5].slug, 3),
    ],
)
def test_seed_detects_identity_conflicts_and_writes_nothing(existing) -> None:
    _insert_tags([existing()])
    before = _tag_rows()

    with SessionLocal() as session:
        with pytest.raises(SeedConflictError):
            plan_initial_tags(session)
    with SessionLocal() as session:
        with pytest.raises(SeedConflictError):
            seed_initial_tags(session, apply=True)

    assert _tag_rows() == before


def test_a_row_overlapping_two_initial_tags_is_a_conflict() -> None:
    _insert_tags([_tag(CONFLICT_TAG_ID, INITIAL_TAGS[0].name, INITIAL_TAGS[1].slug, 3)])

    with SessionLocal() as session:
        with pytest.raises(SeedConflictError):
            seed_initial_tags(session, apply=True)

    assert len(_tag_rows()) == 1


def test_seed_command_is_a_dry_run_unless_apply_is_passed(capsys) -> None:
    assert seed_main([]) == 0
    assert _tag_rows() == []
    assert "Would insert 7" in capsys.readouterr().out

    assert seed_main(["--apply"]) == 0
    assert len(_tag_rows()) == 7
    assert "Inserted 7" in capsys.readouterr().out

    assert seed_main(["--apply"]) == 0
    assert "Inserted 0" in capsys.readouterr().out


def test_seed_command_exits_non_zero_on_conflict(capsys) -> None:
    _insert_tags([_tag(CONFLICT_TAG_ID, INITIAL_TAGS[0].name, "other-slug", 3)])

    assert seed_main(["--apply"]) == 1
    assert "Aborted without writing" in capsys.readouterr().out
    assert len(_tag_rows()) == 1


# ---- Inactive tags keep their existing behaviour (DEC-068 H5 / R1) -------------------------


def _insert_circles_with_inactive_tag() -> None:
    """Circle 0: published revision tagged with an inactive (featured) and an active tag.

    Circle 1: published revision without tags and a draft revision carrying the active tag.
    """

    _insert_tags(
        [
            _tag(ACTIVE_TAG_ID, ACTIVE_NAME, "active-fixture", 1),
            _tag(INACTIVE_TAG_ID, INACTIVE_NAME, "inactive-fixture", 0, is_active=False),
        ]
    )

    def revision(revision_id: UUID, circle_id: UUID, name: str, status: str) -> dict:
        return {
            "id": revision_id,
            "circle_id": circle_id,
            "version_no": 1 if status == "published" else 2,
            "status": status,
            "display_name": name,
            "circle_type": "circle",
            "category_id": CATEGORY_ID,
            "headline": "見出し",
            "summary": "概要",
            "description": "説明",
            "recruiting_status": "open",
            "published_at": PUBLISHED_AT if status == "published" else None,
        }

    with SessionLocal() as session:
        session.execute(
            insert(Category),
            [{"id": CATEGORY_ID, "name": "タグ検証", "slug": "tag-fixture", "display_order": 0}],
        )
        session.execute(
            insert(ProductCircle),
            [
                {
                    "id": circle_id,
                    "slug": f"tag-catalog-{index}",
                    "lifecycle_status": "published",
                    "official_status": "official",
                    "verification_type": "public_unverified",
                    "published_revision_id": None,
                    "deleted_at": None,
                }
                for index, circle_id in enumerate(CIRCLE_IDS)
            ],
        )
        session.execute(
            insert(CircleRevision),
            [
                revision(REVISION_IDS[0], CIRCLE_IDS[0], "Inactive Tag Circle", "published"),
                revision(
                    REVISION_IDS[1],
                    CIRCLE_IDS[1],
                    "Untagged Published Circle",
                    "published",
                )
                | {"published_at": PUBLISHED_AT - timedelta(days=1)},
                revision(REVISION_IDS[2], CIRCLE_IDS[1], "Draft With Active Tag", "draft"),
            ],
        )
        session.execute(
            insert(CircleRevisionTag),
            [
                {
                    "revision_id": REVISION_IDS[0],
                    "tag_id": INACTIVE_TAG_ID,
                    "is_featured": True,
                    "display_order": 0,
                },
                {
                    "revision_id": REVISION_IDS[0],
                    "tag_id": ACTIVE_TAG_ID,
                    "is_featured": False,
                    "display_order": 1,
                },
                {
                    "revision_id": REVISION_IDS[2],
                    "tag_id": ACTIVE_TAG_ID,
                    "is_featured": True,
                    "display_order": 0,
                },
            ],
        )
        for circle_id, revision_id in (
            (CIRCLE_IDS[0], REVISION_IDS[0]),
            (CIRCLE_IDS[1], REVISION_IDS[1]),
        ):
            session.execute(
                update(ProductCircle)
                .where(ProductCircle.id == circle_id)
                .values(published_revision_id=revision_id)
            )
        session.commit()


def _circle_ids(response) -> list[str]:
    assert response.status_code == 200, response.text
    return [item["id"] for item in response.json()["data"]]


def test_inactive_tag_is_hidden_from_the_catalog_but_not_from_existing_reads(
    client: TestClient,
) -> None:
    _insert_circles_with_inactive_tag()

    assert _names(client.get("/api/v1/tags")) == [ACTIVE_NAME]

    detail = client.get(f"/api/v1/circles/{CIRCLE_IDS[0]}").json()["data"]
    assert [(tag["name"], tag["isFeatured"]) for tag in detail["tags"]] == [
        (INACTIVE_NAME, True),
        (ACTIVE_NAME, False),
    ]
    assert [tag["name"] for tag in detail["featuredTags"]] == [INACTIVE_NAME]
    listed = next(
        item
        for item in client.get("/api/v1/circles", params={"limit": 50}).json()["data"]
        if item["id"] == str(CIRCLE_IDS[0])
    )
    assert [tag["id"] for tag in listed["featuredTags"]] == [str(INACTIVE_TAG_ID)]


def test_inactive_tag_still_matches_the_tag_id_filter(client: TestClient) -> None:
    _insert_circles_with_inactive_tag()

    inactive = client.get("/api/v1/circles", params={"tagId": str(INACTIVE_TAG_ID)})
    both = client.get(
        "/api/v1/circles", params={"tagId": [str(INACTIVE_TAG_ID), str(ACTIVE_TAG_ID)]}
    )

    assert _circle_ids(inactive) == [str(CIRCLE_IDS[0])]
    assert inactive.json()["page"]["totalCount"] == 1
    assert _circle_ids(both) == [str(CIRCLE_IDS[0])]


def test_inactive_tag_name_still_matches_the_keyword_search(client: TestClient) -> None:
    _insert_circles_with_inactive_tag()

    response = client.get("/api/v1/circles", params={"q": INACTIVE_NAME})

    assert _circle_ids(response) == [str(CIRCLE_IDS[0])]


def test_draft_revision_tags_stay_private(client: TestClient) -> None:
    _insert_circles_with_inactive_tag()

    by_tag = client.get("/api/v1/circles", params={"tagId": str(ACTIVE_TAG_ID)})
    by_name = client.get("/api/v1/circles", params={"q": ACTIVE_NAME})
    detail = client.get(f"/api/v1/circles/{CIRCLE_IDS[1]}").json()["data"]

    # Circle 1 has the active tag only on a draft revision, so it must never match.
    assert _circle_ids(by_tag) == [str(CIRCLE_IDS[0])]
    assert _circle_ids(by_name) == [str(CIRCLE_IDS[0])]
    assert detail["tags"] == []
    assert detail["featuredTags"] == []
    assert "Draft With Active Tag" not in client.get(f"/api/v1/circles/{CIRCLE_IDS[1]}").text


def test_deactivating_and_seeding_do_not_change_published_revisions(client: TestClient) -> None:
    _insert_circles_with_inactive_tag()
    with SessionLocal() as session:
        revision_tags_before = session.execute(
            select(CircleRevisionTag.revision_id, CircleRevisionTag.tag_id).order_by(
                CircleRevisionTag.revision_id, CircleRevisionTag.tag_id
            )
        ).all()
        published_before = session.execute(
            select(ProductCircle.id, ProductCircle.published_revision_id).order_by(ProductCircle.id)
        ).all()
        session.execute(update(Tag).where(Tag.id == ACTIVE_TAG_ID).values(is_active=False))
        session.commit()
    _seed()

    with SessionLocal() as session:
        revision_tags_after = session.execute(
            select(CircleRevisionTag.revision_id, CircleRevisionTag.tag_id).order_by(
                CircleRevisionTag.revision_id, CircleRevisionTag.tag_id
            )
        ).all()
        published_after = session.execute(
            select(ProductCircle.id, ProductCircle.published_revision_id).order_by(ProductCircle.id)
        ).all()

    assert revision_tags_after == revision_tags_before
    assert published_after == published_before
    detail = client.get(f"/api/v1/circles/{CIRCLE_IDS[0]}").json()["data"]
    assert {tag["name"] for tag in detail["tags"]} == {INACTIVE_NAME, ACTIVE_NAME}
