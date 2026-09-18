from enum import StrEnum
from typing import Protocol
from uuid import UUID

from pydantic import Field, model_validator

from api.models import ApiModel, UtcDateTime

IDEMPOTENCY_KEY_HEADER = "Idempotency-Key"


class IdempotencyState(StrEnum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class IdempotencyContext(ApiModel):
    key: UUID
    actor_id: UUID
    endpoint: str = Field(min_length=1)
    payload_hash: str = Field(min_length=1)


class StoredIdempotencyResult(ApiModel):
    status_code: int = Field(ge=100, le=599)
    response_reference: str | None = None


class IdempotencyRecord(ApiModel):
    context: IdempotencyContext
    state: IdempotencyState
    result: StoredIdempotencyResult | None = None
    expires_at: UtcDateTime


class IdempotencyReservation(ApiModel):
    replay: bool
    result: StoredIdempotencyResult | None = None

    @model_validator(mode="after")
    def replay_requires_result(self) -> "IdempotencyReservation":
        if self.replay and self.result is None:
            raise ValueError("a replay reservation requires a stored result")
        if not self.replay and self.result is not None:
            raise ValueError("a new reservation cannot include a stored result")
        return self


class IdempotencyService(Protocol):
    """Atomic persistence boundary for later idempotent POST integrations.

    Implementations return a new/replay reservation and raise the shared
    REQUEST_IN_PROGRESS or IDEMPOTENCY_KEY_REUSED application errors.
    """

    async def reserve(self, context: IdempotencyContext) -> IdempotencyReservation: ...

    async def complete(
        self,
        context: IdempotencyContext,
        result: StoredIdempotencyResult,
    ) -> None: ...
