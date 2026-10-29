from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app_private.models import Tag


@dataclass(frozen=True)
class TagPosition:
    display_order: int
    tag_id: UUID


@dataclass(frozen=True)
class TagCatalogRecord:
    id: UUID
    name: str
    slug: str
    display_order: int


@dataclass(frozen=True)
class TagPage:
    records: list[TagCatalogRecord]
    has_more: bool


class TagRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_active(self, *, after: TagPosition | None, limit: int) -> TagPage:
        """Return active tags ordered by ``display_order, id`` (keyset paginated).

        ``is_active`` only governs this selectable catalog (DEC-068 H5). Existing revision
        tags, ``tagId`` filtering and ``q`` tag-name search deliberately never read it.
        """

        statement = (
            select(Tag.id, Tag.name, Tag.slug, Tag.display_order)
            .where(Tag.is_active.is_(True))
            .order_by(Tag.display_order, Tag.id)
            .limit(limit + 1)
        )
        if after is not None:
            statement = statement.where(
                or_(
                    Tag.display_order > after.display_order,
                    and_(Tag.display_order == after.display_order, Tag.id > after.tag_id),
                )
            )
        rows = self._session.execute(statement).all()
        records = [
            TagCatalogRecord(
                id=row.id, name=row.name, slug=row.slug, display_order=row.display_order
            )
            for row in rows[:limit]
        ]
        return TagPage(records=records, has_more=len(rows) > limit)
