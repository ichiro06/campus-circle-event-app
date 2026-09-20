from dataclasses import dataclass, field
from datetime import datetime, time
from uuid import UUID

from sqlalchemy import Select, and_, func, literal, or_, select
from sqlalchemy.orm import Session
from sqlalchemy.sql.elements import ColumnElement

from app_private.models import (
    ActivityLocation,
    ActivitySchedule,
    Campus,
    Category,
    Circle,
    CircleCost,
    CircleRevision,
    CircleRevisionTag,
    CircleUniversity,
    Tag,
    University,
)
from circles.schemas import CircleFilters


@dataclass(frozen=True)
class PagePosition:
    published_at: datetime | None
    circle_id: UUID


@dataclass(frozen=True)
class CategoryRecord:
    id: UUID
    name: str
    slug: str


@dataclass(frozen=True)
class UniversityRecord:
    id: UUID
    name: str
    slug: str
    relationship_type: str
    campus: str | None


@dataclass(frozen=True)
class TagRecord:
    id: UUID
    name: str
    slug: str
    is_featured: bool


@dataclass(frozen=True)
class ScheduleRecord:
    weekday: int | None
    time_band: str
    starts_at: time | None
    ends_at: time | None
    note: str | None


@dataclass(frozen=True)
class LocationRecord:
    prefecture: str | None
    city: str | None
    facility_name: str | None
    nearest_station: str | None
    is_online: bool
    public_note: str | None


@dataclass(frozen=True)
class CostRecord:
    cost_type: str
    amount_min_yen: int
    amount_max_yen: int | None
    label: str
    note: str | None


@dataclass
class CircleRecord:
    id: UUID
    revision_id: UUID
    display_name: str
    headline: str
    summary: str
    official_status: str
    circle_type: str
    published_at: datetime | None
    category: CategoryRecord
    description: str
    recruiting_status: str
    member_count_band: str | None
    camp_frequency_code: str | None
    activity_frequency_code: str | None
    drinking_frequency_rating: int | None
    liveliness_rating: int | None
    commitment_rating: int | None
    attendance_flexibility_rating: int | None
    career_opportunity_rating: int | None
    gender_balance_code: str | None
    universities: list[UniversityRecord] = field(default_factory=list)
    featured_tags: list[TagRecord] = field(default_factory=list)
    activity_schedules: list[ScheduleRecord] = field(default_factory=list)
    activity_locations: list[LocationRecord] = field(default_factory=list)
    tags: list[TagRecord] = field(default_factory=list)
    costs: list[CostRecord] = field(default_factory=list)


@dataclass(frozen=True)
class CirclePage:
    records: list[CircleRecord]
    has_more: bool
    total_count: int


def _escaped_like_pattern(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def public_visibility_predicates() -> tuple[ColumnElement[bool], ...]:
    """The one public visibility predicate shared by list and detail."""

    return (
        Circle.deleted_at.is_(None),
        Circle.lifecycle_status == "published",
        Circle.published_revision_id.is_not(None),
        CircleRevision.id == Circle.published_revision_id,
        CircleRevision.circle_id == Circle.id,
        CircleRevision.status == "published",
    )


class CircleRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_public(
        self,
        *,
        filters: CircleFilters,
        after: PagePosition | None,
        limit: int,
    ) -> CirclePage:
        total_count = int(self._session.scalar(self.build_count_statement(filters)) or 0)
        rows = list(
            self._session.execute(
                self.build_list_statement(filters=filters, after=after, limit=limit + 1)
            ).mappings()
        )
        has_more = len(rows) > limit
        records = self._hydrate(rows[:limit], include_detail=False)
        return CirclePage(records=records, has_more=has_more, total_count=total_count)

    def get_public(self, circle_id: UUID) -> CircleRecord | None:
        statement = self._base_statement().where(
            *public_visibility_predicates(),
            Circle.id == circle_id,
        )
        row = self._session.execute(statement).mappings().one_or_none()
        if row is None:
            return None
        return self._hydrate([row], include_detail=True)[0]

    def build_count_statement(self, filters: CircleFilters) -> Select[tuple[int]]:
        predicates = [*public_visibility_predicates(), *self._filter_predicates(filters)]
        return (
            select(func.count())
            .select_from(Circle)
            .join(CircleRevision, CircleRevision.id == Circle.published_revision_id)
            .where(*predicates)
        )

    def build_list_statement(
        self,
        *,
        filters: CircleFilters,
        after: PagePosition | None,
        limit: int,
    ) -> Select:
        predicates = [*public_visibility_predicates(), *self._filter_predicates(filters)]
        if after is not None:
            predicates.append(self._keyset_predicate(after))
        return (
            self._base_statement()
            .where(*predicates)
            .order_by(CircleRevision.published_at.desc().nulls_last(), Circle.id.desc())
            .limit(limit)
        )

    @staticmethod
    def _base_statement() -> Select:
        return (
            select(
                Circle.id.label("circle_id"),
                CircleRevision.id.label("revision_id"),
                CircleRevision.display_name,
                CircleRevision.headline,
                CircleRevision.summary,
                Circle.official_status,
                CircleRevision.circle_type,
                CircleRevision.published_at,
                Category.id.label("category_id"),
                Category.name.label("category_name"),
                Category.slug.label("category_slug"),
                CircleRevision.description,
                CircleRevision.recruiting_status,
                CircleRevision.member_count_band,
                CircleRevision.camp_frequency_code,
                CircleRevision.activity_frequency_code,
                CircleRevision.drinking_frequency_rating,
                CircleRevision.liveliness_rating,
                CircleRevision.commitment_rating,
                CircleRevision.attendance_flexibility_rating,
                CircleRevision.career_opportunity_rating,
                CircleRevision.gender_balance_code,
            )
            .select_from(Circle)
            .join(CircleRevision, CircleRevision.id == Circle.published_revision_id)
            .join(Category, Category.id == CircleRevision.category_id)
        )

    @staticmethod
    def _filter_predicates(filters: CircleFilters) -> list[ColumnElement[bool]]:
        predicates: list[ColumnElement[bool]] = []
        if filters.official_statuses:
            predicates.append(Circle.official_status.in_(filters.official_statuses))
        if filters.circle_types:
            predicates.append(CircleRevision.circle_type.in_(filters.circle_types))
        if filters.camp_frequency_codes:
            predicates.append(CircleRevision.camp_frequency_code.in_(filters.camp_frequency_codes))
        if filters.member_count_bands:
            predicates.append(CircleRevision.member_count_band.in_(filters.member_count_bands))
        if filters.activity_frequency_codes:
            predicates.append(
                CircleRevision.activity_frequency_code.in_(filters.activity_frequency_codes)
            )
        if filters.gender_balance_codes:
            predicates.append(CircleRevision.gender_balance_code.in_(filters.gender_balance_codes))
        if filters.tag_ids:
            predicates.append(
                select(literal(1))
                .select_from(CircleRevisionTag)
                .where(
                    CircleRevisionTag.revision_id == CircleRevision.id,
                    CircleRevisionTag.tag_id.in_(filters.tag_ids),
                )
                .exists()
            )
        if filters.weekdays:
            weekday_numbers = [int(value) for value in filters.weekdays if value != "irregular"]
            weekday_options: list[ColumnElement[bool]] = []
            if weekday_numbers:
                weekday_options.append(ActivitySchedule.weekday.in_(weekday_numbers))
            if "irregular" in filters.weekdays:
                weekday_options.append(ActivitySchedule.weekday.is_(None))
            predicates.append(
                select(literal(1))
                .select_from(ActivitySchedule)
                .where(
                    ActivitySchedule.revision_id == CircleRevision.id,
                    or_(*weekday_options),
                )
                .exists()
            )
        if filters.time_bands:
            predicates.append(
                select(literal(1))
                .select_from(ActivitySchedule)
                .where(
                    ActivitySchedule.revision_id == CircleRevision.id,
                    ActivitySchedule.time_band.in_(filters.time_bands),
                )
                .exists()
            )
        if filters.q is not None:
            pattern = _escaped_like_pattern(filters.q)
            university_match = (
                select(literal(1))
                .select_from(CircleUniversity)
                .join(University, University.id == CircleUniversity.university_id)
                .outerjoin(Campus, Campus.id == CircleUniversity.campus_id)
                .where(
                    CircleUniversity.circle_id == Circle.id,
                    or_(
                        University.name.ilike(pattern, escape="\\"),
                        Campus.name.ilike(pattern, escape="\\"),
                    ),
                )
                .exists()
            )
            tag_match = (
                select(literal(1))
                .select_from(CircleRevisionTag)
                .join(Tag, Tag.id == CircleRevisionTag.tag_id)
                .where(
                    CircleRevisionTag.revision_id == CircleRevision.id,
                    Tag.name.ilike(pattern, escape="\\"),
                )
                .exists()
            )
            location_match = (
                select(literal(1))
                .select_from(ActivityLocation)
                .where(
                    ActivityLocation.revision_id == CircleRevision.id,
                    or_(
                        ActivityLocation.prefecture.ilike(pattern, escape="\\"),
                        ActivityLocation.city.ilike(pattern, escape="\\"),
                        ActivityLocation.facility_name.ilike(pattern, escape="\\"),
                        ActivityLocation.nearest_station.ilike(pattern, escape="\\"),
                        ActivityLocation.public_note.ilike(pattern, escape="\\"),
                    ),
                )
                .exists()
            )
            predicates.append(
                or_(
                    CircleRevision.display_name.ilike(pattern, escape="\\"),
                    CircleRevision.headline.ilike(pattern, escape="\\"),
                    CircleRevision.summary.ilike(pattern, escape="\\"),
                    CircleRevision.description.ilike(pattern, escape="\\"),
                    university_match,
                    tag_match,
                    location_match,
                )
            )
        return predicates

    @staticmethod
    def _keyset_predicate(after: PagePosition) -> ColumnElement[bool]:
        if after.published_at is None:
            return and_(
                CircleRevision.published_at.is_(None),
                Circle.id < after.circle_id,
            )
        return or_(
            CircleRevision.published_at < after.published_at,
            and_(
                CircleRevision.published_at == after.published_at,
                Circle.id < after.circle_id,
            ),
            CircleRevision.published_at.is_(None),
        )

    def _hydrate(self, rows: list, *, include_detail: bool) -> list[CircleRecord]:
        records = [
            CircleRecord(
                id=row["circle_id"],
                revision_id=row["revision_id"],
                display_name=row["display_name"],
                headline=row["headline"],
                summary=row["summary"],
                official_status=row["official_status"],
                circle_type=row["circle_type"],
                published_at=row["published_at"],
                category=CategoryRecord(
                    id=row["category_id"],
                    name=row["category_name"],
                    slug=row["category_slug"],
                ),
                description=row["description"],
                recruiting_status=row["recruiting_status"],
                member_count_band=row["member_count_band"],
                camp_frequency_code=row["camp_frequency_code"],
                activity_frequency_code=row["activity_frequency_code"],
                drinking_frequency_rating=row["drinking_frequency_rating"],
                liveliness_rating=row["liveliness_rating"],
                commitment_rating=row["commitment_rating"],
                attendance_flexibility_rating=row["attendance_flexibility_rating"],
                career_opportunity_rating=row["career_opportunity_rating"],
                gender_balance_code=row["gender_balance_code"],
            )
            for row in rows
        ]
        if not records:
            return records

        by_circle = {record.id: record for record in records}
        by_revision = {record.revision_id: record for record in records}
        circle_ids = tuple(by_circle)
        revision_ids = tuple(by_revision)
        self._load_universities(by_circle, circle_ids)
        self._load_tags(by_revision, revision_ids, include_all=include_detail)
        self._load_schedules(by_revision, revision_ids)
        self._load_locations(by_revision, revision_ids)
        if include_detail:
            self._load_costs(by_revision, revision_ids)
        return records

    def _load_universities(
        self,
        records: dict[UUID, CircleRecord],
        circle_ids: tuple[UUID, ...],
    ) -> None:
        statement = (
            select(
                CircleUniversity.circle_id,
                University.id,
                University.name,
                University.slug,
                CircleUniversity.relationship_type,
                Campus.name.label("campus_name"),
            )
            .select_from(CircleUniversity)
            .join(University, University.id == CircleUniversity.university_id)
            .outerjoin(Campus, Campus.id == CircleUniversity.campus_id)
            .where(CircleUniversity.circle_id.in_(circle_ids))
            .order_by(
                CircleUniversity.circle_id,
                CircleUniversity.relationship_type,
                University.name,
                Campus.name.asc().nulls_last(),
                University.id,
            )
        )
        for row in self._session.execute(statement).mappings():
            records[row["circle_id"]].universities.append(
                UniversityRecord(
                    id=row["id"],
                    name=row["name"],
                    slug=row["slug"],
                    relationship_type=row["relationship_type"],
                    campus=row["campus_name"],
                )
            )

    def _load_tags(
        self,
        records: dict[UUID, CircleRecord],
        revision_ids: tuple[UUID, ...],
        *,
        include_all: bool,
    ) -> None:
        statement = (
            select(
                CircleRevisionTag.revision_id,
                Tag.id,
                Tag.name,
                Tag.slug,
                CircleRevisionTag.is_featured,
            )
            .select_from(CircleRevisionTag)
            .join(Tag, Tag.id == CircleRevisionTag.tag_id)
            .where(CircleRevisionTag.revision_id.in_(revision_ids))
            .order_by(
                CircleRevisionTag.revision_id,
                CircleRevisionTag.display_order,
                Tag.display_order,
                Tag.id,
            )
        )
        if not include_all:
            statement = statement.where(CircleRevisionTag.is_featured.is_(True))
        for row in self._session.execute(statement).mappings():
            record = records[row["revision_id"]]
            tag = TagRecord(
                id=row["id"],
                name=row["name"],
                slug=row["slug"],
                is_featured=row["is_featured"],
            )
            if include_all:
                record.tags.append(tag)
            if tag.is_featured and len(record.featured_tags) < 5:
                record.featured_tags.append(tag)

    def _load_schedules(
        self,
        records: dict[UUID, CircleRecord],
        revision_ids: tuple[UUID, ...],
    ) -> None:
        statement = (
            select(
                ActivitySchedule.revision_id,
                ActivitySchedule.weekday,
                ActivitySchedule.time_band,
                ActivitySchedule.starts_at,
                ActivitySchedule.ends_at,
                ActivitySchedule.note,
            )
            .where(ActivitySchedule.revision_id.in_(revision_ids))
            .order_by(
                ActivitySchedule.revision_id,
                ActivitySchedule.display_order,
                ActivitySchedule.id,
            )
        )
        for row in self._session.execute(statement).mappings():
            records[row["revision_id"]].activity_schedules.append(
                ScheduleRecord(
                    weekday=row["weekday"],
                    time_band=row["time_band"],
                    starts_at=row["starts_at"],
                    ends_at=row["ends_at"],
                    note=row["note"],
                )
            )

    def _load_locations(
        self,
        records: dict[UUID, CircleRecord],
        revision_ids: tuple[UUID, ...],
    ) -> None:
        statement = (
            select(
                ActivityLocation.revision_id,
                ActivityLocation.prefecture,
                ActivityLocation.city,
                ActivityLocation.facility_name,
                ActivityLocation.nearest_station,
                ActivityLocation.is_online,
                ActivityLocation.public_note,
            )
            .where(ActivityLocation.revision_id.in_(revision_ids))
            .order_by(
                ActivityLocation.revision_id,
                ActivityLocation.display_order,
                ActivityLocation.id,
            )
        )
        for row in self._session.execute(statement).mappings():
            records[row["revision_id"]].activity_locations.append(
                LocationRecord(
                    prefecture=row["prefecture"],
                    city=row["city"],
                    facility_name=row["facility_name"],
                    nearest_station=row["nearest_station"],
                    is_online=row["is_online"],
                    public_note=row["public_note"],
                )
            )

    def _load_costs(
        self,
        records: dict[UUID, CircleRecord],
        revision_ids: tuple[UUID, ...],
    ) -> None:
        statement = (
            select(
                CircleCost.revision_id,
                CircleCost.cost_type,
                CircleCost.amount_min_yen,
                CircleCost.amount_max_yen,
                CircleCost.label,
                CircleCost.note,
            )
            .where(CircleCost.revision_id.in_(revision_ids))
            .order_by(CircleCost.revision_id, CircleCost.display_order, CircleCost.id)
        )
        for row in self._session.execute(statement).mappings():
            records[row["revision_id"]].costs.append(
                CostRecord(
                    cost_type=row["cost_type"],
                    amount_min_yen=row["amount_min_yen"],
                    amount_max_yen=row["amount_max_yen"],
                    label=row["label"],
                    note=row["note"],
                )
            )
