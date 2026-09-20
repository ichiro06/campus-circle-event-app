from datetime import datetime, time
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, SmallInteger, String, Text, Time
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

SCHEMA = "app_private"


class ProductBase(DeclarativeBase):
    """Metadata for Alembic-managed product tables.

    This metadata is intentionally separate from the prototype metadata in
    ``database.Base`` and must never be passed to ``create_all()``.
    """


class University(ProductBase):
    __tablename__ = "universities"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(80), nullable=False)


class Campus(ProductBase):
    __tablename__ = "campuses"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True)
    university_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.universities.id"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(80), nullable=False)


class Category(ProductBase):
    __tablename__ = "categories"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    slug: Mapped[str] = mapped_column(String(80), nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False)


class Tag(ProductBase):
    __tablename__ = "tags"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    slug: Mapped[str] = mapped_column(String(80), nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False)


class Circle(ProductBase):
    __tablename__ = "circles"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    lifecycle_status: Mapped[str] = mapped_column(String(20), nullable=False)
    official_status: Mapped[str] = mapped_column(String(16), nullable=False)
    verification_type: Mapped[str] = mapped_column(String(24), nullable=False)
    published_revision_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.circle_revisions.id"),
        nullable=True,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class CircleUniversity(ProductBase):
    __tablename__ = "circle_universities"
    __table_args__ = {"schema": SCHEMA}

    circle_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.circles.id"),
        primary_key=True,
    )
    university_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.universities.id"),
        primary_key=True,
    )
    campus_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.campuses.id"),
        nullable=True,
    )
    relationship_type: Mapped[str] = mapped_column(String(20), primary_key=True)


class CircleRevision(ProductBase):
    __tablename__ = "circle_revisions"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True)
    circle_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.circles.id"),
        nullable=False,
    )
    version_no: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    circle_type: Mapped[str] = mapped_column(String(24), nullable=False)
    category_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.categories.id"),
        nullable=False,
    )
    headline: Mapped[str] = mapped_column(String(100), nullable=False)
    summary: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    recruiting_status: Mapped[str] = mapped_column(String(16), nullable=False)
    member_count_band: Mapped[str | None] = mapped_column(String(20), nullable=True)
    camp_frequency_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    activity_frequency_code: Mapped[str | None] = mapped_column(String(24), nullable=True)
    drinking_frequency_rating: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    liveliness_rating: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    commitment_rating: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    attendance_flexibility_rating: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    career_opportunity_rating: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    gender_balance_code: Mapped[str | None] = mapped_column(String(24), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class CircleRevisionTag(ProductBase):
    __tablename__ = "circle_revision_tags"
    __table_args__ = {"schema": SCHEMA}

    revision_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.circle_revisions.id"),
        primary_key=True,
    )
    tag_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.tags.id"),
        primary_key=True,
    )
    is_featured: Mapped[bool] = mapped_column(Boolean, nullable=False)
    display_order: Mapped[int] = mapped_column(SmallInteger, nullable=False)


class ActivitySchedule(ProductBase):
    __tablename__ = "activity_schedules"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True)
    revision_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.circle_revisions.id"),
        nullable=False,
    )
    weekday: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    time_band: Mapped[str] = mapped_column(String(16), nullable=False)
    starts_at: Mapped[time | None] = mapped_column(Time, nullable=True)
    ends_at: Mapped[time | None] = mapped_column(Time, nullable=True)
    note: Mapped[str | None] = mapped_column(String(200), nullable=True)
    display_order: Mapped[int] = mapped_column(SmallInteger, nullable=False)


class ActivityLocation(ProductBase):
    __tablename__ = "activity_locations"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True)
    revision_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.circle_revisions.id"),
        nullable=False,
    )
    prefecture: Mapped[str | None] = mapped_column(String(40), nullable=True)
    city: Mapped[str | None] = mapped_column(String(80), nullable=True)
    facility_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    nearest_station: Mapped[str | None] = mapped_column(String(120), nullable=True)
    is_online: Mapped[bool] = mapped_column(Boolean, nullable=False)
    public_note: Mapped[str | None] = mapped_column(String(300), nullable=True)
    display_order: Mapped[int] = mapped_column(SmallInteger, nullable=False)


class CircleCost(ProductBase):
    __tablename__ = "circle_costs"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True)
    revision_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.circle_revisions.id"),
        nullable=False,
    )
    cost_type: Mapped[str] = mapped_column(String(16), nullable=False)
    amount_min_yen: Mapped[int] = mapped_column(Integer, nullable=False)
    amount_max_yen: Mapped[int | None] = mapped_column(Integer, nullable=True)
    label: Mapped[str] = mapped_column(String(80), nullable=False)
    note: Mapped[str | None] = mapped_column(String(300), nullable=True)
    display_order: Mapped[int] = mapped_column(SmallInteger, nullable=False)
