"""Create the initial private product schema.

Revision ID: 20260915_0001
Revises:
Create Date: 2026-09-15

The existing public circles/events tables are technical verification data and
are deliberately left untouched.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260915_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SCHEMA = "app_private"


def uuid_column(name: str = "id", *, nullable: bool = False) -> sa.Column:
    return sa.Column(
        name,
        postgresql.UUID(as_uuid=True),
        nullable=nullable,
        server_default=sa.text("gen_random_uuid()") if name == "id" else None,
    )


def timestamps() -> tuple[sa.Column, sa.Column]:
    return (
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )


def upgrade() -> None:
    op.execute(sa.text(f'CREATE SCHEMA IF NOT EXISTS "{SCHEMA}"'))

    op.create_table(
        "universities",
        uuid_column(),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("slug", sa.String(80), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        *timestamps(),
        sa.PrimaryKeyConstraint("id", name="pk_universities"),
        sa.UniqueConstraint("name", name="uq_universities_name"),
        sa.UniqueConstraint("slug", name="uq_universities_slug"),
        schema=SCHEMA,
    )
    op.create_table(
        "campuses",
        uuid_column(),
        uuid_column("university_id"),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("slug", sa.String(80), nullable=False),
        sa.Column("prefecture", sa.String(40), nullable=True),
        sa.Column("city", sa.String(80), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        *timestamps(),
        sa.ForeignKeyConstraint(
            ["university_id"],
            [f"{SCHEMA}.universities.id"],
            name="fk_campuses_university",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_campuses"),
        sa.UniqueConstraint("university_id", "slug", name="uq_campuses_university_slug"),
        schema=SCHEMA,
    )
    op.create_index("ix_campuses_university", "campuses", ["university_id"], schema=SCHEMA)

    for table_name in ("categories", "tags"):
        op.create_table(
            table_name,
            uuid_column(),
            sa.Column("name", sa.String(80), nullable=False),
            sa.Column("slug", sa.String(80), nullable=False),
            sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            *timestamps(),
            sa.CheckConstraint("display_order >= 0", name=f"ck_{table_name}_display_order"),
            sa.PrimaryKeyConstraint("id", name=f"pk_{table_name}"),
            sa.UniqueConstraint("name", name=f"uq_{table_name}_name"),
            sa.UniqueConstraint("slug", name=f"uq_{table_name}_slug"),
            schema=SCHEMA,
        )

    op.create_table(
        "accounts",
        uuid_column(),
        sa.Column("status", sa.String(24), nullable=False, server_default="active"),
        sa.Column(
            "history_collection_enabled", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column("terms_accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("privacy_notice_version", sa.String(40), nullable=True),
        sa.Column("deletion_requested_at", sa.DateTime(timezone=True), nullable=True),
        *timestamps(),
        sa.CheckConstraint(
            "status IN ('active', 'suspended', 'deletion_pending', 'deleted')",
            name="ck_accounts_status",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_accounts"),
        schema=SCHEMA,
    )

    op.create_table(
        "profiles",
        uuid_column("user_id"),
        sa.Column("nickname", sa.String(40), nullable=True),
        uuid_column("avatar_asset_id", nullable=True),
        uuid_column("university_id", nullable=True),
        sa.Column("school_year_code", sa.String(24), nullable=True),
        sa.Column("onboarding_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.CheckConstraint(
            "nickname IS NULL OR char_length(btrim(nickname)) BETWEEN 2 AND 40",
            name="ck_profiles_nickname_length",
        ),
        sa.CheckConstraint(
            "school_year_code IS NULL OR school_year_code IN "
            "('undergrad_1', 'undergrad_2', 'undergrad_3', 'undergrad_4', "
            "'undergrad_5', 'undergrad_6', 'master_1', 'master_2', 'doctoral', "
            "'other', 'not_disclosed')",
            name="ck_profiles_school_year",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            [f"{SCHEMA}.accounts.id"],
            name="fk_profiles_account",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["university_id"],
            [f"{SCHEMA}.universities.id"],
            name="fk_profiles_university",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("user_id", name="pk_profiles"),
        schema=SCHEMA,
    )

    op.create_table(
        "profile_interests",
        uuid_column("user_id"),
        uuid_column("category_id"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            [f"{SCHEMA}.accounts.id"],
            name="fk_profile_interests_account",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["category_id"],
            [f"{SCHEMA}.categories.id"],
            name="fk_profile_interests_category",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("user_id", "category_id", name="pk_profile_interests"),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_profile_interests_category", "profile_interests", ["category_id"], schema=SCHEMA
    )

    op.create_table(
        "service_operators",
        uuid_column("user_id"),
        sa.Column("status", sa.String(16), nullable=False, server_default="active"),
        sa.Column("mfa_verified_at", sa.DateTime(timezone=True), nullable=True),
        uuid_column("granted_by_user_id", nullable=True),
        sa.Column("grant_reason", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('active', 'suspended', 'revoked')",
            name="ck_service_operators_status",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            [f"{SCHEMA}.accounts.id"],
            name="fk_service_operators_account",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["granted_by_user_id"],
            [f"{SCHEMA}.accounts.id"],
            name="fk_service_operators_granted_by",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("user_id", name="pk_service_operators"),
        schema=SCHEMA,
    )

    op.create_table(
        "circles",
        uuid_column(),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("lifecycle_status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("official_status", sa.String(16), nullable=False, server_default="unknown"),
        sa.Column(
            "verification_type", sa.String(24), nullable=False, server_default="public_unverified"
        ),
        uuid_column("published_revision_id", nullable=True),
        uuid_column("created_by_user_id", nullable=True),
        *timestamps(),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "lifecycle_status IN ('draft', 'in_review', 'published', 'suspended', 'archived')",
            name="ck_circles_lifecycle_status",
        ),
        sa.CheckConstraint(
            "official_status IN ('official', 'unofficial', 'unknown')",
            name="ck_circles_official_status",
        ),
        sa.CheckConstraint(
            "verification_type IN ('official_public', 'public_unverified', 'private')",
            name="ck_circles_verification_type",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            [f"{SCHEMA}.accounts.id"],
            name="fk_circles_created_by",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_circles"),
        sa.UniqueConstraint("slug", name="uq_circles_slug"),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_circles_publication", "circles", ["lifecycle_status", "deleted_at"], schema=SCHEMA
    )

    op.create_table(
        "media_assets",
        uuid_column(),
        uuid_column("owner_user_id", nullable=True),
        uuid_column("owner_circle_id", nullable=True),
        sa.Column("storage_bucket", sa.String(80), nullable=False),
        sa.Column("object_key", sa.String(500), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("checksum_sha256", sa.String(64), nullable=False),
        sa.Column("scan_status", sa.String(16), nullable=False, server_default="pending"),
        *timestamps(),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("size_bytes > 0", name="ck_media_assets_size"),
        sa.CheckConstraint("width IS NULL OR width > 0", name="ck_media_assets_width"),
        sa.CheckConstraint("height IS NULL OR height > 0", name="ck_media_assets_height"),
        sa.CheckConstraint(
            "scan_status IN ('pending', 'clean', 'rejected', 'failed')",
            name="ck_media_assets_scan_status",
        ),
        sa.ForeignKeyConstraint(
            ["owner_user_id"],
            [f"{SCHEMA}.accounts.id"],
            name="fk_media_assets_owner_user",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["owner_circle_id"],
            [f"{SCHEMA}.circles.id"],
            name="fk_media_assets_owner_circle",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_media_assets"),
        sa.UniqueConstraint("storage_bucket", "object_key", name="uq_media_assets_object"),
        schema=SCHEMA,
    )
    op.create_foreign_key(
        "fk_profiles_avatar_asset",
        "profiles",
        "media_assets",
        ["avatar_asset_id"],
        ["id"],
        source_schema=SCHEMA,
        referent_schema=SCHEMA,
        ondelete="SET NULL",
    )

    op.create_table(
        "circle_universities",
        uuid_column("circle_id"),
        uuid_column("university_id"),
        uuid_column("campus_id", nullable=True),
        sa.Column("relationship_type", sa.String(20), nullable=False),
        sa.ForeignKeyConstraint(
            ["circle_id"],
            [f"{SCHEMA}.circles.id"],
            name="fk_circle_universities_circle",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["university_id"],
            [f"{SCHEMA}.universities.id"],
            name="fk_circle_universities_university",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["campus_id"],
            [f"{SCHEMA}.campuses.id"],
            name="fk_circle_universities_campus",
            ondelete="SET NULL",
        ),
        sa.CheckConstraint(
            "relationship_type IN ('primary', 'participating', 'activity_base')",
            name="ck_circle_universities_relationship",
        ),
        sa.PrimaryKeyConstraint(
            "circle_id", "university_id", "relationship_type", name="pk_circle_universities"
        ),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_circle_universities_university",
        "circle_universities",
        ["university_id"],
        schema=SCHEMA,
    )

    op.create_table(
        "circle_revisions",
        uuid_column(),
        uuid_column("circle_id"),
        sa.Column("version_no", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="draft"),
        sa.Column("display_name", sa.String(120), nullable=False),
        sa.Column("circle_type", sa.String(24), nullable=False),
        uuid_column("category_id"),
        sa.Column("headline", sa.String(100), nullable=False),
        sa.Column("summary", sa.String(300), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("recruiting_status", sa.String(16), nullable=False, server_default="unknown"),
        sa.Column("member_count_band", sa.String(20), nullable=True),
        sa.Column("camp_frequency_code", sa.String(20), nullable=True),
        sa.Column("activity_frequency_code", sa.String(24), nullable=True),
        sa.Column("annual_cost_min_yen", sa.Integer(), nullable=True),
        sa.Column("annual_cost_max_yen", sa.Integer(), nullable=True),
        sa.Column("drinking_frequency_rating", sa.SmallInteger(), nullable=True),
        sa.Column("liveliness_rating", sa.SmallInteger(), nullable=True),
        sa.Column("commitment_rating", sa.SmallInteger(), nullable=True),
        sa.Column("attendance_flexibility_rating", sa.SmallInteger(), nullable=True),
        sa.Column("career_opportunity_rating", sa.SmallInteger(), nullable=True),
        sa.Column("gender_balance_code", sa.String(24), nullable=True),
        uuid_column("submitted_by_user_id", nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        uuid_column("reviewed_by_user_id", nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_note", sa.Text(), nullable=True),
        *timestamps(),
        sa.CheckConstraint("version_no > 0", name="ck_circle_revisions_version"),
        sa.CheckConstraint(
            "status IN ('draft', 'in_review', 'changes_requested', 'approved', "
            "'published', 'rejected', 'superseded')",
            name="ck_circle_revisions_status",
        ),
        sa.CheckConstraint(
            "circle_type IN ('circle', 'club', 'intercollegiate', 'student_organization')",
            name="ck_circle_revisions_type",
        ),
        sa.CheckConstraint(
            "recruiting_status IN ('open', 'seasonal', 'closed', 'unknown')",
            name="ck_circle_revisions_recruiting",
        ),
        sa.CheckConstraint(
            "member_count_band IS NULL OR member_count_band IN "
            "('1_10', '11_30', '31_80', '81_150', '151_plus', 'not_disclosed')",
            name="ck_circle_revisions_member_count",
        ),
        sa.CheckConstraint(
            "camp_frequency_code IS NULL OR camp_frequency_code IN "
            "('none', 'once_year', 'twice_year', 'three_plus_year', 'unknown')",
            name="ck_circle_revisions_camp_frequency",
        ),
        sa.CheckConstraint(
            "activity_frequency_code IS NULL OR activity_frequency_code IN "
            "('less_monthly', 'monthly', 'two_three_monthly', 'weekly', "
            "'two_three_weekly', 'four_plus_weekly', 'irregular')",
            name="ck_circle_revisions_activity_frequency",
        ),
        sa.CheckConstraint(
            "annual_cost_min_yen IS NULL OR annual_cost_min_yen >= 0",
            name="ck_circle_revisions_cost_min",
        ),
        sa.CheckConstraint(
            "annual_cost_max_yen IS NULL OR annual_cost_max_yen >= 0",
            name="ck_circle_revisions_cost_max",
        ),
        sa.CheckConstraint(
            "annual_cost_min_yen IS NULL OR annual_cost_max_yen IS NULL "
            "OR annual_cost_min_yen <= annual_cost_max_yen",
            name="ck_circle_revisions_cost_order",
        ),
        sa.CheckConstraint(
            "drinking_frequency_rating IS NULL OR drinking_frequency_rating BETWEEN 1 AND 5",
            name="ck_circle_revisions_drinking_rating",
        ),
        sa.CheckConstraint(
            "liveliness_rating IS NULL OR liveliness_rating BETWEEN 1 AND 5",
            name="ck_circle_revisions_liveliness_rating",
        ),
        sa.CheckConstraint(
            "commitment_rating IS NULL OR commitment_rating BETWEEN 1 AND 5",
            name="ck_circle_revisions_commitment_rating",
        ),
        sa.CheckConstraint(
            "attendance_flexibility_rating IS NULL "
            "OR attendance_flexibility_rating BETWEEN 1 AND 5",
            name="ck_circle_revisions_attendance_rating",
        ),
        sa.CheckConstraint(
            "career_opportunity_rating IS NULL OR career_opportunity_rating BETWEEN 1 AND 5",
            name="ck_circle_revisions_career_rating",
        ),
        sa.CheckConstraint(
            "gender_balance_code IS NULL OR gender_balance_code IN "
            "('women_majority', 'balanced', 'men_majority', 'mixed_or_other', 'not_disclosed')",
            name="ck_circle_revisions_gender_balance",
        ),
        sa.ForeignKeyConstraint(
            ["circle_id"],
            [f"{SCHEMA}.circles.id"],
            name="fk_circle_revisions_circle",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["category_id"],
            [f"{SCHEMA}.categories.id"],
            name="fk_circle_revisions_category",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["submitted_by_user_id"],
            [f"{SCHEMA}.accounts.id"],
            name="fk_circle_revisions_submitted_by",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["reviewed_by_user_id"],
            [f"{SCHEMA}.service_operators.user_id"],
            name="fk_circle_revisions_reviewed_by",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_circle_revisions"),
        sa.UniqueConstraint("circle_id", "version_no", name="uq_circle_revisions_version"),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_circle_revisions_circle_status",
        "circle_revisions",
        ["circle_id", "status"],
        schema=SCHEMA,
    )
    op.create_index(
        "ix_circle_revisions_category_published",
        "circle_revisions",
        ["category_id", "published_at", "id"],
        schema=SCHEMA,
    )
    op.create_foreign_key(
        "fk_circles_published_revision",
        "circles",
        "circle_revisions",
        ["published_revision_id"],
        ["id"],
        source_schema=SCHEMA,
        referent_schema=SCHEMA,
        ondelete="SET NULL",
    )

    op.create_table(
        "circle_revision_tags",
        uuid_column("revision_id"),
        uuid_column("tag_id"),
        sa.Column("is_featured", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("display_order", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.CheckConstraint("display_order >= 0", name="ck_circle_revision_tags_order"),
        sa.ForeignKeyConstraint(
            ["revision_id"],
            [f"{SCHEMA}.circle_revisions.id"],
            name="fk_circle_revision_tags_revision",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tag_id"],
            [f"{SCHEMA}.tags.id"],
            name="fk_circle_revision_tags_tag",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("revision_id", "tag_id", name="pk_circle_revision_tags"),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_circle_revision_tags_tag", "circle_revision_tags", ["tag_id"], schema=SCHEMA
    )

    op.create_table(
        "activity_schedules",
        uuid_column(),
        uuid_column("revision_id"),
        sa.Column("weekday", sa.SmallInteger(), nullable=True),
        sa.Column("time_band", sa.String(16), nullable=False),
        sa.Column("starts_at", sa.Time(), nullable=True),
        sa.Column("ends_at", sa.Time(), nullable=True),
        sa.Column("note", sa.String(200), nullable=True),
        sa.Column("display_order", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.CheckConstraint(
            "weekday IS NULL OR weekday BETWEEN 1 AND 7", name="ck_schedules_weekday"
        ),
        sa.CheckConstraint(
            "time_band IN ('morning', 'daytime', 'evening', 'night', 'all_day', 'irregular')",
            name="ck_schedules_time_band",
        ),
        sa.CheckConstraint(
            "starts_at IS NULL OR ends_at IS NULL OR starts_at < ends_at",
            name="ck_schedules_time_order",
        ),
        sa.CheckConstraint("display_order >= 0", name="ck_schedules_order"),
        sa.ForeignKeyConstraint(
            ["revision_id"],
            [f"{SCHEMA}.circle_revisions.id"],
            name="fk_schedules_revision",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_activity_schedules"),
        schema=SCHEMA,
    )
    op.create_index("ix_schedules_revision", "activity_schedules", ["revision_id"], schema=SCHEMA)

    op.create_table(
        "activity_locations",
        uuid_column(),
        uuid_column("revision_id"),
        sa.Column("prefecture", sa.String(40), nullable=True),
        sa.Column("city", sa.String(80), nullable=True),
        sa.Column("facility_name", sa.String(150), nullable=True),
        sa.Column("nearest_station", sa.String(120), nullable=True),
        sa.Column("is_online", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("public_note", sa.String(300), nullable=True),
        sa.Column("display_order", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.CheckConstraint("display_order >= 0", name="ck_locations_order"),
        sa.ForeignKeyConstraint(
            ["revision_id"],
            [f"{SCHEMA}.circle_revisions.id"],
            name="fk_locations_revision",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_activity_locations"),
        schema=SCHEMA,
    )
    op.create_index("ix_locations_revision", "activity_locations", ["revision_id"], schema=SCHEMA)

    op.create_table(
        "circle_costs",
        uuid_column(),
        uuid_column("revision_id"),
        sa.Column("cost_type", sa.String(16), nullable=False),
        sa.Column("amount_min_yen", sa.Integer(), nullable=False),
        sa.Column("amount_max_yen", sa.Integer(), nullable=True),
        sa.Column("label", sa.String(80), nullable=False),
        sa.Column("note", sa.String(300), nullable=True),
        sa.Column("display_order", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.CheckConstraint(
            "cost_type IN ('admission', 'annual', 'monthly', 'per_event', 'other')",
            name="ck_circle_costs_type",
        ),
        sa.CheckConstraint("amount_min_yen >= 0", name="ck_circle_costs_min"),
        sa.CheckConstraint(
            "amount_max_yen IS NULL OR amount_max_yen >= amount_min_yen",
            name="ck_circle_costs_order",
        ),
        sa.CheckConstraint("display_order >= 0", name="ck_circle_costs_display_order"),
        sa.ForeignKeyConstraint(
            ["revision_id"],
            [f"{SCHEMA}.circle_revisions.id"],
            name="fk_circle_costs_revision",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_circle_costs"),
        schema=SCHEMA,
    )
    op.create_index("ix_circle_costs_revision", "circle_costs", ["revision_id"], schema=SCHEMA)

    op.create_table(
        "social_links",
        uuid_column(),
        uuid_column("revision_id"),
        sa.Column("service", sa.String(16), nullable=False),
        sa.Column("url", sa.String(1000), nullable=False),
        sa.Column("display_order", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.CheckConstraint(
            "service IN ('instagram', 'line', 'website', 'other')",
            name="ck_social_links_service",
        ),
        sa.CheckConstraint("display_order >= 0", name="ck_social_links_order"),
        sa.ForeignKeyConstraint(
            ["revision_id"],
            [f"{SCHEMA}.circle_revisions.id"],
            name="fk_social_links_revision",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_social_links"),
        schema=SCHEMA,
    )
    op.create_index("ix_social_links_revision", "social_links", ["revision_id"], schema=SCHEMA)

    op.create_table(
        "circle_revision_media",
        uuid_column("revision_id"),
        uuid_column("asset_id"),
        sa.Column("role", sa.String(12), nullable=False),
        sa.Column("alt_text", sa.String(200), nullable=False),
        sa.Column("display_order", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.CheckConstraint("role IN ('cover', 'gallery')", name="ck_revision_media_role"),
        sa.CheckConstraint("display_order >= 0", name="ck_revision_media_order"),
        sa.ForeignKeyConstraint(
            ["revision_id"],
            [f"{SCHEMA}.circle_revisions.id"],
            name="fk_revision_media_revision",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["asset_id"],
            [f"{SCHEMA}.media_assets.id"],
            name="fk_revision_media_asset",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("revision_id", "asset_id", name="pk_circle_revision_media"),
        schema=SCHEMA,
    )
    op.create_index("ix_revision_media_asset", "circle_revision_media", ["asset_id"], schema=SCHEMA)

    op.create_table(
        "favorites",
        uuid_column("user_id"),
        uuid_column("circle_id"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            [f"{SCHEMA}.accounts.id"],
            name="fk_favorites_account",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["circle_id"],
            [f"{SCHEMA}.circles.id"],
            name="fk_favorites_circle",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("user_id", "circle_id", name="pk_favorites"),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_favorites_circle_created", "favorites", ["circle_id", "created_at"], schema=SCHEMA
    )

    op.create_table(
        "circle_views",
        uuid_column(),
        uuid_column("user_id"),
        uuid_column("circle_id"),
        sa.Column(
            "viewed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("is_counted", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("excluded_reason", sa.String(40), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            [f"{SCHEMA}.accounts.id"],
            name="fk_circle_views_account",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["circle_id"],
            [f"{SCHEMA}.circles.id"],
            name="fk_circle_views_circle",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_circle_views"),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_circle_views_user_time", "circle_views", ["user_id", "viewed_at"], schema=SCHEMA
    )
    op.create_index(
        "ix_circle_views_user_circle_time",
        "circle_views",
        ["user_id", "circle_id", "viewed_at"],
        schema=SCHEMA,
    )

    op.create_table(
        "manager_applications",
        uuid_column(),
        uuid_column("applicant_user_id"),
        uuid_column("circle_id", nullable=True),
        sa.Column("status", sa.String(24), nullable=False, server_default="submitted"),
        sa.Column("verification_method", sa.String(40), nullable=True),
        sa.Column("relationship_description", sa.Text(), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("additional_information_due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        uuid_column("reviewed_by_user_id", nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decision_reason", sa.Text(), nullable=True),
        sa.Column("appeal_requested_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("appeal_decided_at", sa.DateTime(timezone=True), nullable=True),
        *timestamps(),
        sa.CheckConstraint(
            "status IN ('submitted', 'evidence_requested', 'under_review', 'approved', "
            "'rejected', 'withdrawn', 'expired', 'appealed')",
            name="ck_manager_applications_status",
        ),
        sa.ForeignKeyConstraint(
            ["applicant_user_id"],
            [f"{SCHEMA}.accounts.id"],
            name="fk_manager_applications_applicant",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["circle_id"],
            [f"{SCHEMA}.circles.id"],
            name="fk_manager_applications_circle",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["reviewed_by_user_id"],
            [f"{SCHEMA}.service_operators.user_id"],
            name="fk_manager_applications_reviewer",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_manager_applications"),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_manager_applications_applicant_status",
        "manager_applications",
        ["applicant_user_id", "status"],
        schema=SCHEMA,
    )
    op.create_index(
        "ix_manager_applications_circle_status",
        "manager_applications",
        ["circle_id", "status"],
        schema=SCHEMA,
    )

    op.create_table(
        "manager_evidence",
        uuid_column(),
        uuid_column("application_id"),
        sa.Column("evidence_type", sa.String(40), nullable=False),
        sa.Column("reference_url", sa.String(1000), nullable=True),
        sa.Column("storage_object_key", sa.String(500), nullable=True),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column(
            "submitted_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delete_after", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "reference_url IS NOT NULL OR storage_object_key IS NOT NULL",
            name="ck_manager_evidence_reference",
        ),
        sa.ForeignKeyConstraint(
            ["application_id"],
            [f"{SCHEMA}.manager_applications.id"],
            name="fk_manager_evidence_application",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_manager_evidence"),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_manager_evidence_application",
        "manager_evidence",
        ["application_id"],
        schema=SCHEMA,
    )
    op.create_index(
        "ix_manager_evidence_delete_after",
        "manager_evidence",
        ["delete_after"],
        schema=SCHEMA,
    )

    op.create_table(
        "manager_invitations",
        uuid_column(),
        uuid_column("circle_id"),
        uuid_column("invited_by_user_id"),
        uuid_column("target_user_id", nullable=True),
        sa.Column("target_email_hmac", sa.String(64), nullable=True),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="pending"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.CheckConstraint(
            "target_user_id IS NOT NULL OR target_email_hmac IS NOT NULL",
            name="ck_manager_invitations_target",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'accepted', 'expired', 'revoked')",
            name="ck_manager_invitations_status",
        ),
        sa.ForeignKeyConstraint(
            ["circle_id"],
            [f"{SCHEMA}.circles.id"],
            name="fk_manager_invitations_circle",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["invited_by_user_id"],
            [f"{SCHEMA}.accounts.id"],
            name="fk_manager_invitations_inviter",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["target_user_id"],
            [f"{SCHEMA}.accounts.id"],
            name="fk_manager_invitations_target_user",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_manager_invitations"),
        sa.UniqueConstraint("token_hash", name="uq_manager_invitations_token_hash"),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_manager_invitations_circle_status",
        "manager_invitations",
        ["circle_id", "status"],
        schema=SCHEMA,
    )

    op.create_table(
        "circle_memberships",
        uuid_column(),
        uuid_column("user_id"),
        uuid_column("circle_id"),
        sa.Column("role", sa.String(16), nullable=False, server_default="manager"),
        sa.Column("status", sa.String(16), nullable=False, server_default="active"),
        uuid_column("application_id", nullable=True),
        sa.Column(
            "starts_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        uuid_column("revoked_by_user_id", nullable=True),
        sa.Column("revocation_reason", sa.Text(), nullable=True),
        *timestamps(),
        sa.CheckConstraint("role = 'manager'", name="ck_circle_memberships_role"),
        sa.CheckConstraint(
            "status IN ('active', 'suspended', 'revoked', 'expired')",
            name="ck_circle_memberships_status",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            [f"{SCHEMA}.accounts.id"],
            name="fk_circle_memberships_account",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["circle_id"],
            [f"{SCHEMA}.circles.id"],
            name="fk_circle_memberships_circle",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["application_id"],
            [f"{SCHEMA}.manager_applications.id"],
            name="fk_circle_memberships_application",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["revoked_by_user_id"],
            [f"{SCHEMA}.accounts.id"],
            name="fk_circle_memberships_revoked_by",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_circle_memberships"),
        schema=SCHEMA,
    )
    op.create_index(
        "uq_circle_memberships_active",
        "circle_memberships",
        ["user_id", "circle_id"],
        unique=True,
        schema=SCHEMA,
        postgresql_where=sa.text("status = 'active'"),
    )
    op.create_index(
        "ix_circle_memberships_circle_status",
        "circle_memberships",
        ["circle_id", "status"],
        schema=SCHEMA,
    )

    op.create_table(
        "reports",
        uuid_column(),
        uuid_column("reporter_user_id"),
        uuid_column("circle_id"),
        sa.Column("category", sa.String(32), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="submitted"),
        uuid_column("assigned_operator_user_id", nullable=True),
        sa.Column("decision_reason", sa.Text(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        *timestamps(),
        sa.CheckConstraint(
            "category IN ('inappropriate', 'false_information', 'dangerous', 'solicitation', "
            "'impersonation', 'personal_information', 'other')",
            name="ck_reports_category",
        ),
        sa.CheckConstraint(
            "status IN ('submitted', 'triaged', 'investigating', 'resolved', 'dismissed')",
            name="ck_reports_status",
        ),
        sa.ForeignKeyConstraint(
            ["reporter_user_id"],
            [f"{SCHEMA}.accounts.id"],
            name="fk_reports_reporter",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["circle_id"],
            [f"{SCHEMA}.circles.id"],
            name="fk_reports_circle",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["assigned_operator_user_id"],
            [f"{SCHEMA}.service_operators.user_id"],
            name="fk_reports_operator",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_reports"),
        schema=SCHEMA,
    )
    op.create_index("ix_reports_status_created", "reports", ["status", "created_at"], schema=SCHEMA)

    op.create_table(
        "audit_logs",
        uuid_column(),
        uuid_column("actor_user_id", nullable=True),
        sa.Column("actor_type", sa.String(16), nullable=False),
        sa.Column("action", sa.String(80), nullable=False),
        sa.Column("target_type", sa.String(60), nullable=False),
        uuid_column("target_id", nullable=True),
        uuid_column("circle_id", nullable=True),
        sa.Column("before_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("after_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("reason", sa.String(500), nullable=True),
        uuid_column("request_id", nullable=True),
        sa.Column("result", sa.String(16), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.CheckConstraint(
            "actor_type IN ('user', 'manager', 'operator', 'system')",
            name="ck_audit_logs_actor_type",
        ),
        sa.CheckConstraint(
            "result IN ('success', 'denied', 'failed')", name="ck_audit_logs_result"
        ),
        sa.ForeignKeyConstraint(
            ["actor_user_id"],
            [f"{SCHEMA}.accounts.id"],
            name="fk_audit_logs_actor",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["circle_id"],
            [f"{SCHEMA}.circles.id"],
            name="fk_audit_logs_circle",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_audit_logs"),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_audit_logs_target_time",
        "audit_logs",
        ["target_type", "target_id", "created_at"],
        schema=SCHEMA,
    )
    op.create_index(
        "ix_audit_logs_circle_time", "audit_logs", ["circle_id", "created_at"], schema=SCHEMA
    )

    op.create_table(
        "idempotency_records",
        uuid_column(),
        uuid_column("actor_user_id"),
        sa.Column("endpoint", sa.String(200), nullable=False),
        uuid_column("idempotency_key"),
        sa.Column("payload_hash", sa.String(64), nullable=False),
        sa.Column("processing_status", sa.String(16), nullable=False, server_default="processing"),
        sa.Column("response_status", sa.SmallInteger(), nullable=True),
        sa.Column("resource_type", sa.String(60), nullable=True),
        uuid_column("resource_id", nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "processing_status IN ('processing', 'completed', 'failed')",
            name="ck_idempotency_records_status",
        ),
        sa.CheckConstraint(
            "response_status IS NULL OR response_status BETWEEN 100 AND 599",
            name="ck_idempotency_records_response_status",
        ),
        sa.ForeignKeyConstraint(
            ["actor_user_id"],
            [f"{SCHEMA}.accounts.id"],
            name="fk_idempotency_records_actor",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_idempotency_records"),
        sa.UniqueConstraint(
            "actor_user_id", "endpoint", "idempotency_key", name="uq_idempotency_records_key"
        ),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_idempotency_records_expiry",
        "idempotency_records",
        ["expires_at"],
        schema=SCHEMA,
    )


def downgrade() -> None:
    op.drop_table("idempotency_records", schema=SCHEMA)
    op.drop_table("audit_logs", schema=SCHEMA)
    op.drop_table("reports", schema=SCHEMA)
    op.drop_table("circle_memberships", schema=SCHEMA)
    op.drop_table("manager_invitations", schema=SCHEMA)
    op.drop_table("manager_evidence", schema=SCHEMA)
    op.drop_table("manager_applications", schema=SCHEMA)
    op.drop_table("circle_views", schema=SCHEMA)
    op.drop_table("favorites", schema=SCHEMA)
    op.drop_table("circle_revision_media", schema=SCHEMA)
    op.drop_table("social_links", schema=SCHEMA)
    op.drop_table("circle_costs", schema=SCHEMA)
    op.drop_table("activity_locations", schema=SCHEMA)
    op.drop_table("activity_schedules", schema=SCHEMA)
    op.drop_table("circle_revision_tags", schema=SCHEMA)
    op.drop_constraint(
        "fk_circles_published_revision", "circles", schema=SCHEMA, type_="foreignkey"
    )
    op.drop_table("circle_revisions", schema=SCHEMA)
    op.drop_table("circle_universities", schema=SCHEMA)
    op.drop_constraint("fk_profiles_avatar_asset", "profiles", schema=SCHEMA, type_="foreignkey")
    op.drop_table("media_assets", schema=SCHEMA)
    op.drop_table("circles", schema=SCHEMA)
    op.drop_table("service_operators", schema=SCHEMA)
    op.drop_table("profile_interests", schema=SCHEMA)
    op.drop_table("profiles", schema=SCHEMA)
    op.drop_table("accounts", schema=SCHEMA)
    op.drop_table("tags", schema=SCHEMA)
    op.drop_table("categories", schema=SCHEMA)
    op.drop_table("campuses", schema=SCHEMA)
    op.drop_table("universities", schema=SCHEMA)
    op.execute(sa.text(f'DROP SCHEMA IF EXISTS "{SCHEMA}"'))
