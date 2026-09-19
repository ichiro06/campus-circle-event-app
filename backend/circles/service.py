from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.orm import Session

from api.errors import ApplicationError, InvalidCursorError
from circles.cursor import SignedCircleCursorCodec
from circles.repository import CircleRecord, CircleRepository, PagePosition
from circles.schemas import (
    ActivityLocationRead,
    ActivityScheduleRead,
    CategoryRead,
    CircleCostRead,
    CircleDetail,
    CircleFilters,
    CircleListItem,
    CircleListQuery,
    CirclePageMetadata,
    FeaturedTagRead,
    TagRead,
    UniversityRead,
    WeekdayValue,
)


@dataclass(frozen=True)
class CircleListResult:
    data: list[CircleListItem]
    page: CirclePageMetadata


class CircleReadService:
    def __init__(self, session: Session, cursor_codec: SignedCircleCursorCodec) -> None:
        self._repository = CircleRepository(session)
        self._cursor_codec = cursor_codec

    def list_public(self, query: CircleListQuery) -> CircleListResult:
        filters = query.normalized_filters()
        position = self._validate_cursor(query.cursor, filters) if query.cursor else None
        result = self._repository.list_public(
            filters=filters,
            after=position,
            limit=query.limit,
        )
        next_cursor = None
        if result.has_more:
            last_record = result.records[-1]
            next_cursor = self._cursor_codec.encode(
                last_published_at=last_record.published_at,
                last_circle_id=last_record.id,
                filters=filters.cursor_binding(),
            )
        return CircleListResult(
            data=[self._list_item(record) for record in result.records],
            page=CirclePageMetadata(
                next_cursor=next_cursor,
                has_more=result.has_more,
                limit=query.limit,
                total_count=result.total_count,
            ),
        )

    def get_public(self, circle_id: UUID) -> CircleDetail:
        record = self._repository.get_public(circle_id)
        if record is None:
            raise ApplicationError("NOT_FOUND")
        return CircleDetail(
            **self._list_item(record).model_dump(),
            description=record.description,
            recruiting_status=record.recruiting_status,
            member_count_band=record.member_count_band,
            camp_frequency_code=record.camp_frequency_code,
            activity_frequency_code=record.activity_frequency_code,
            drinking_frequency_rating=record.drinking_frequency_rating,
            liveliness_rating=record.liveliness_rating,
            commitment_rating=record.commitment_rating,
            attendance_flexibility_rating=record.attendance_flexibility_rating,
            career_opportunity_rating=record.career_opportunity_rating,
            gender_balance_code=record.gender_balance_code,
            tags=[
                TagRead(
                    id=tag.id,
                    name=tag.name,
                    slug=tag.slug,
                    is_featured=tag.is_featured,
                )
                for tag in record.tags
            ],
            costs=[
                CircleCostRead(
                    cost_type=cost.cost_type,
                    amount_min_yen=cost.amount_min_yen,
                    amount_max_yen=cost.amount_max_yen,
                    label=cost.label,
                    note=cost.note,
                )
                for cost in record.costs
            ],
        )

    def _validate_cursor(
        self,
        cursor: str,
        filters: CircleFilters,
    ) -> PagePosition:
        payload = self._cursor_codec.decode(cursor)
        if payload.sort != "newest" or payload.filters != filters.cursor_binding():
            raise InvalidCursorError()
        return PagePosition(
            published_at=payload.last_published_at,
            circle_id=payload.last_circle_id,
        )

    @staticmethod
    def _list_item(record: CircleRecord) -> CircleListItem:
        return CircleListItem(
            id=record.id,
            display_name=record.display_name,
            headline=record.headline,
            summary=record.summary,
            official_status=record.official_status,
            circle_type=record.circle_type,
            published_at=record.published_at,
            category=CategoryRead(
                id=record.category.id,
                name=record.category.name,
                slug=record.category.slug,
            ),
            universities=[
                UniversityRead(
                    id=university.id,
                    name=university.name,
                    slug=university.slug,
                    relationship_type=university.relationship_type,
                    campus=university.campus,
                )
                for university in record.universities
            ],
            featured_tags=[
                FeaturedTagRead(id=tag.id, name=tag.name, slug=tag.slug)
                for tag in record.featured_tags
            ],
            activity_schedules=[
                ActivityScheduleRead(
                    weekday=(
                        WeekdayValue.irregular
                        if schedule.weekday is None
                        else WeekdayValue(str(schedule.weekday))
                    ),
                    time_band=schedule.time_band,
                    starts_at=schedule.starts_at,
                    ends_at=schedule.ends_at,
                    note=schedule.note,
                )
                for schedule in record.activity_schedules
            ],
            activity_locations=[
                ActivityLocationRead(
                    prefecture=location.prefecture,
                    city=location.city,
                    facility_name=location.facility_name,
                    nearest_station=location.nearest_station,
                    is_online=location.is_online,
                    public_note=location.public_note,
                )
                for location in record.activity_locations
            ],
        )


def build_circle_read_service(session: Session) -> CircleReadService:
    return CircleReadService(session, SignedCircleCursorCodec.from_environment())
