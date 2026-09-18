from typing import Protocol

from pydantic import Field

from api.models import DEFAULT_PAGE_LIMIT, MAX_PAGE_LIMIT, ApiModel


class PaginationParams(ApiModel):
    cursor: str | None = Field(default=None, min_length=1)
    limit: int = Field(default=DEFAULT_PAGE_LIMIT, ge=1, le=MAX_PAGE_LIMIT)


class CursorCodec[CursorPayloadT](Protocol):
    """Replaceable boundary for Work 2's signed, filter-bound cursor."""

    def encode(self, payload: CursorPayloadT) -> str: ...

    def decode(self, cursor: str) -> CursorPayloadT: ...
