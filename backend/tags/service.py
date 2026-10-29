from dataclasses import dataclass

from sqlalchemy.orm import Session

from api.models import PageMetadata
from tags.cursor import SignedTagCursorCodec
from tags.repository import TagPosition, TagRepository
from tags.schemas import TagCatalogItem, TagListQuery


@dataclass(frozen=True)
class TagListResult:
    data: list[TagCatalogItem]
    page: PageMetadata


class TagCatalogService:
    def __init__(self, session: Session) -> None:
        self._repository = TagRepository(session)

    def list_public(self, query: TagListQuery) -> TagListResult:
        # The signing secret is only needed to read or issue a cursor, so a first page that
        # fits in one response does not depend on it.
        position = None
        if query.cursor is not None:
            payload = SignedTagCursorCodec.from_environment().decode(query.cursor)
            position = TagPosition(
                display_order=payload.last_display_order,
                tag_id=payload.last_tag_id,
            )
        page = self._repository.list_active(after=position, limit=query.limit)
        next_cursor = None
        if page.has_more:
            last_record = page.records[-1]
            next_cursor = SignedTagCursorCodec.from_environment().encode(
                last_display_order=last_record.display_order,
                last_tag_id=last_record.id,
            )
        return TagListResult(
            data=[
                TagCatalogItem(id=record.id, name=record.name, slug=record.slug)
                for record in page.records
            ],
            page=PageMetadata(next_cursor=next_cursor, has_more=page.has_more, limit=query.limit),
        )
