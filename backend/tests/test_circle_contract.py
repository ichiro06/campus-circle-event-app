from datetime import UTC, datetime
from typing import cast
from uuid import UUID

import pytest
from pydantic import ValidationError
from sqlalchemy.orm import Session

from api.errors import InvalidCursorError
from api.models import PageMetadata
from app_private.models import ProductBase
from circles.cursor import SignedCircleCursorCodec
from circles.repository import CirclePage, PagePosition
from circles.schemas import CircleListQuery, CirclePageMetadata
from circles.service import CircleReadService
from database import Base
from models import Circle as PrototypeCircle

TEST_SECRET = b"fixed-test-cursor-secret-32-bytes!"
NOW = datetime(2026, 9, 19, tzinfo=UTC)


class RecordingRepository:
    def __init__(self) -> None:
        self.after: PagePosition | None = None

    def list_public(self, *, filters, after, limit: int) -> CirclePage:
        self.after = after
        return CirclePage(records=[], has_more=False, total_count=0)


def test_query_normalization_deduplicates_and_sorts_repeated_filters() -> None:
    first_tag = UUID(int=1)
    second_tag = UUID(int=2)
    query = CircleListQuery(
        q="  音楽  ",
        official_status=["unknown", "official", "official"],
        weekday=["irregular", "1", "1"],
        tag_id=[second_tag, first_tag, second_tag],
    )

    filters = query.normalized_filters()
    assert filters.q == "音楽"
    assert filters.official_statuses == ("official", "unknown")
    assert filters.weekdays == ("1", "irregular")
    assert filters.tag_ids == (first_tag, second_tag)


def test_explicit_blank_q_is_invalid() -> None:
    with pytest.raises(ValidationError):
        CircleListQuery(q=" \t ")


def test_only_newest_sort_and_approved_weekdays_are_accepted() -> None:
    assert CircleListQuery(sort="newest", weekday=["1", "7", "irregular"])
    with pytest.raises(ValidationError):
        CircleListQuery(sort="recommended")
    with pytest.raises(ValidationError):
        CircleListQuery(weekday=["0"])
    with pytest.raises(ValidationError):
        CircleListQuery(weekday=["monday"])


def test_circle_page_extends_only_the_circle_contract() -> None:
    circle_page = CirclePageMetadata(has_more=False, limit=20, total_count=12)
    assert circle_page.model_dump() == {
        "hasMore": False,
        "limit": 20,
        "totalCount": 12,
    }
    assert "totalCount" not in PageMetadata(has_more=False, limit=20).model_dump()

    with pytest.raises(ValidationError):
        CirclePageMetadata(has_more=True, limit=20, total_count=12)
    with pytest.raises(ValidationError):
        CirclePageMetadata(
            next_cursor="unexpected",
            has_more=False,
            limit=20,
            total_count=12,
        )


def test_formal_metadata_is_separate_and_schema_qualified() -> None:
    assert ProductBase.metadata is not Base.metadata
    assert ProductBase.metadata.tables
    assert all(table.schema == "app_private" for table in ProductBase.metadata.tables.values())
    assert PrototypeCircle.metadata is Base.metadata
    assert "circles" in Base.metadata.tables
    assert "app_private.circles" in ProductBase.metadata.tables


def test_service_rejects_filter_mismatch_before_querying() -> None:
    codec = SignedCircleCursorCodec(TEST_SECRET, clock=lambda: NOW)
    cursor = codec.encode(
        last_published_at=None,
        last_circle_id=UUID(int=10),
        filters=CircleListQuery(official_status=["official"]).normalized_filters().cursor_binding(),
    )
    service = CircleReadService(cast(Session, None), codec)
    repository = RecordingRepository()
    service._repository = repository  # type: ignore[assignment]

    with pytest.raises(InvalidCursorError):
        service.list_public(CircleListQuery(cursor=cursor, official_status=["unofficial"]))
    assert repository.after is None


def test_service_accepts_a_valid_nullable_sort_position() -> None:
    codec = SignedCircleCursorCodec(TEST_SECRET, clock=lambda: NOW)
    query = CircleListQuery()
    cursor = codec.encode(
        last_published_at=None,
        last_circle_id=UUID(int=10),
        filters=query.normalized_filters().cursor_binding(),
    )
    service = CircleReadService(cast(Session, None), codec)
    repository = RecordingRepository()
    service._repository = repository  # type: ignore[assignment]

    result = service.list_public(CircleListQuery(cursor=cursor))

    assert result.data == []
    assert result.page.total_count == 0
    assert repository.after == PagePosition(published_at=None, circle_id=UUID(int=10))
