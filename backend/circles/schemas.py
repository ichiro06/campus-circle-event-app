from dataclasses import dataclass
from datetime import time
from enum import StrEnum
from typing import Literal
from uuid import UUID

from pydantic import Field, field_validator, model_validator

from api.models import (
    DEFAULT_PAGE_LIMIT,
    MAX_PAGE_LIMIT,
    ApiModel,
    RequestMetadata,
    UtcDateTime,
)


class OfficialStatus(StrEnum):
    official = "official"
    unofficial = "unofficial"
    unknown = "unknown"


class CircleType(StrEnum):
    circle = "circle"
    club = "club"
    intercollegiate = "intercollegiate"
    student_organization = "student_organization"


class RecruitingStatus(StrEnum):
    open = "open"
    seasonal = "seasonal"
    closed = "closed"
    unknown = "unknown"


class MemberCountBand(StrEnum):
    one_to_ten = "1_10"
    eleven_to_thirty = "11_30"
    thirty_one_to_eighty = "31_80"
    eighty_one_to_one_hundred_fifty = "81_150"
    one_hundred_fifty_one_plus = "151_plus"
    not_disclosed = "not_disclosed"


class CampFrequencyCode(StrEnum):
    none = "none"
    once_year = "once_year"
    twice_year = "twice_year"
    three_plus_year = "three_plus_year"
    unknown = "unknown"


class ActivityFrequencyCode(StrEnum):
    less_monthly = "less_monthly"
    monthly = "monthly"
    two_three_monthly = "two_three_monthly"
    weekly = "weekly"
    two_three_weekly = "two_three_weekly"
    four_plus_weekly = "four_plus_weekly"
    irregular = "irregular"


class GenderBalanceCode(StrEnum):
    women_majority = "women_majority"
    balanced = "balanced"
    men_majority = "men_majority"
    mixed_or_other = "mixed_or_other"
    not_disclosed = "not_disclosed"


class RelationshipType(StrEnum):
    primary = "primary"
    participating = "participating"
    activity_base = "activity_base"


class WeekdayValue(StrEnum):
    monday = "1"
    tuesday = "2"
    wednesday = "3"
    thursday = "4"
    friday = "5"
    saturday = "6"
    sunday = "7"
    irregular = "irregular"


class TimeBand(StrEnum):
    morning = "morning"
    daytime = "daytime"
    evening = "evening"
    night = "night"
    all_day = "all_day"
    irregular = "irregular"


class CostType(StrEnum):
    admission = "admission"
    annual = "annual"
    monthly = "monthly"
    per_event = "per_event"
    other = "other"


class CircleSort(StrEnum):
    newest = "newest"


def _normalized_values(values: list[StrEnum]) -> tuple[str, ...]:
    return tuple(sorted({value.value for value in values}))


@dataclass(frozen=True)
class CircleFilters:
    q: str | None
    official_statuses: tuple[str, ...]
    circle_types: tuple[str, ...]
    camp_frequency_codes: tuple[str, ...]
    member_count_bands: tuple[str, ...]
    activity_frequency_codes: tuple[str, ...]
    weekdays: tuple[str, ...]
    time_bands: tuple[str, ...]
    tag_ids: tuple[UUID, ...]
    gender_balance_codes: tuple[str, ...]

    def cursor_binding(self) -> dict[str, str | list[str] | None]:
        return {
            "q": self.q,
            "officialStatus": list(self.official_statuses),
            "circleType": list(self.circle_types),
            "campFrequencyCode": list(self.camp_frequency_codes),
            "memberCountBand": list(self.member_count_bands),
            "activityFrequencyCode": list(self.activity_frequency_codes),
            "weekday": list(self.weekdays),
            "timeBand": list(self.time_bands),
            "tagId": [str(value) for value in self.tag_ids],
            "genderBalanceCode": list(self.gender_balance_codes),
        }


class CircleListQuery(ApiModel):
    q: str | None = None
    official_status: list[OfficialStatus] = Field(default_factory=list)
    circle_type: list[CircleType] = Field(default_factory=list)
    camp_frequency_code: list[CampFrequencyCode] = Field(default_factory=list)
    member_count_band: list[MemberCountBand] = Field(default_factory=list)
    activity_frequency_code: list[ActivityFrequencyCode] = Field(default_factory=list)
    weekday: list[WeekdayValue] = Field(default_factory=list)
    time_band: list[TimeBand] = Field(default_factory=list)
    tag_id: list[UUID] = Field(default_factory=list)
    gender_balance_code: list[GenderBalanceCode] = Field(default_factory=list)
    sort: CircleSort = CircleSort.newest
    cursor: str | None = Field(default=None, min_length=1)
    limit: int = Field(default=DEFAULT_PAGE_LIMIT, ge=1, le=MAX_PAGE_LIMIT)

    @field_validator("q")
    @classmethod
    def trim_non_empty_query(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            raise ValueError("q must not be blank")
        return normalized

    def normalized_filters(self) -> CircleFilters:
        return CircleFilters(
            q=self.q,
            official_statuses=_normalized_values(self.official_status),
            circle_types=_normalized_values(self.circle_type),
            camp_frequency_codes=_normalized_values(self.camp_frequency_code),
            member_count_bands=_normalized_values(self.member_count_band),
            activity_frequency_codes=_normalized_values(self.activity_frequency_code),
            weekdays=_normalized_values(self.weekday),
            time_bands=_normalized_values(self.time_band),
            tag_ids=tuple(sorted(set(self.tag_id), key=str)),
            gender_balance_codes=_normalized_values(self.gender_balance_code),
        )


class CategoryRead(ApiModel):
    id: UUID
    name: str
    slug: str


class UniversityRead(ApiModel):
    id: UUID
    name: str
    slug: str
    relationship_type: RelationshipType
    campus: str | None


class FeaturedTagRead(ApiModel):
    id: UUID
    name: str
    slug: str


class TagRead(FeaturedTagRead):
    is_featured: bool


class ActivityScheduleRead(ApiModel):
    weekday: WeekdayValue
    time_band: TimeBand
    starts_at: time | None
    ends_at: time | None
    note: str | None


class ActivityLocationRead(ApiModel):
    prefecture: str | None
    city: str | None
    facility_name: str | None
    nearest_station: str | None
    is_online: bool
    public_note: str | None


class CircleCostRead(ApiModel):
    cost_type: CostType
    amount_min_yen: int = Field(ge=0)
    amount_max_yen: int | None = Field(ge=0)
    label: str
    note: str | None


class CircleListItem(ApiModel):
    id: UUID
    display_name: str
    headline: str
    summary: str
    official_status: OfficialStatus
    circle_type: CircleType
    published_at: UtcDateTime | None
    category: CategoryRead
    universities: list[UniversityRead]
    featured_tags: list[FeaturedTagRead] = Field(max_length=5)
    activity_schedules: list[ActivityScheduleRead]
    activity_locations: list[ActivityLocationRead]


class CircleDetail(CircleListItem):
    description: str
    recruiting_status: RecruitingStatus
    member_count_band: MemberCountBand | None
    camp_frequency_code: CampFrequencyCode | None
    activity_frequency_code: ActivityFrequencyCode | None
    drinking_frequency_rating: int | None = Field(ge=1, le=5)
    liveliness_rating: int | None = Field(ge=1, le=5)
    commitment_rating: int | None = Field(ge=1, le=5)
    attendance_flexibility_rating: int | None = Field(ge=1, le=5)
    career_opportunity_rating: int | None = Field(ge=1, le=5)
    gender_balance_code: GenderBalanceCode | None
    tags: list[TagRead]
    costs: list[CircleCostRead]


class CirclePageMetadata(ApiModel):
    next_cursor: str | None = Field(
        default=None,
        min_length=1,
        exclude_if=lambda value: value is None,
    )
    has_more: bool
    limit: int = Field(ge=1, le=MAX_PAGE_LIMIT)
    total_count: int = Field(ge=0)

    @model_validator(mode="after")
    def cursor_presence_matches_has_more(self) -> "CirclePageMetadata":
        if self.has_more != (self.next_cursor is not None):
            raise ValueError("next_cursor must be present if and only if has_more is true")
        return self


class CircleCollectionResponse(ApiModel):
    data: list[CircleListItem]
    page: CirclePageMetadata
    meta: RequestMetadata


NewestSort = Literal["newest"]
