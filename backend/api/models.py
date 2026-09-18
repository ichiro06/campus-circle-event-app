from datetime import UTC, datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, model_validator

DEFAULT_PAGE_LIMIT = 20
MAX_PAGE_LIMIT = 50


def to_camel(value: str) -> str:
    first, *rest = value.split("_")
    return first + "".join(word.capitalize() for word in rest)


def _normalize_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("datetime must include a timezone")
    return value.astimezone(UTC)


UtcDateTime = Annotated[datetime, AfterValidator(_normalize_utc)]


class ApiModel(BaseModel):
    """Base model for the formal wire contract.

    Python and database fields remain snake_case while validation locations and
    serialized JSON use camelCase aliases.
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        extra="forbid",
        from_attributes=True,
        loc_by_alias=True,
        serialize_by_alias=True,
        validate_by_alias=True,
        validate_by_name=True,
    )


class RequestMetadata(ApiModel):
    request_id: UUID


class SuccessResponse[DataT](ApiModel):
    data: DataT
    meta: RequestMetadata


class PageMetadata(ApiModel):
    next_cursor: str | None = Field(
        default=None,
        min_length=1,
        exclude_if=lambda value: value is None,
    )
    has_more: bool
    limit: int = Field(ge=1, le=MAX_PAGE_LIMIT)

    @model_validator(mode="after")
    def cursor_presence_matches_has_more(self) -> "PageMetadata":
        if self.has_more != (self.next_cursor is not None):
            raise ValueError("next_cursor must be present if and only if has_more is true")
        return self


class CollectionResponse[ItemT](ApiModel):
    data: list[ItemT]
    page: PageMetadata
    meta: RequestMetadata


class ProblemFieldError(ApiModel):
    field: str = Field(min_length=1)
    code: str = Field(min_length=1)


class ProblemDetails(ApiModel):
    type: str = Field(default="about:blank", min_length=1)
    title: str = Field(min_length=1)
    status: int = Field(ge=100, le=599)
    detail: str = Field(min_length=1)
    instance: str = Field(min_length=1)
    code: str = Field(min_length=1)
    request_id: UUID
    errors: list[ProblemFieldError] | None = Field(
        default=None,
        exclude_if=lambda value: value is None,
    )


class ApiHealth(ApiModel):
    status: Literal["ok"] = "ok"
    api_version: Literal["v1"] = "v1"
