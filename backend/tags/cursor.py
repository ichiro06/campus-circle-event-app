import hashlib
import hmac
import json
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import Field, ValidationError

from api.errors import InvalidCursorError
from api.models import ApiModel
from circles.cursor import (
    CURSOR_TTL_SECONDS,
    MINIMUM_SECRET_BYTES,
    _decode_base64url,
    _encode_base64url,
    load_cursor_signing_secret,
)

TAG_CURSOR_VERSION = 1


class TagCursorPayload(ApiModel):
    """Signed (not encrypted) keyset position for the public tag catalog.

    ``resource`` keeps tag cursors and Circle cursors from being accepted by each other's
    endpoint: the payload models forbid unknown fields, so neither validates as the other.
    """

    version: Literal[1]
    resource: Literal["tags"]
    last_display_order: int = Field(ge=0, strict=True)
    last_tag_id: UUID
    issued_at: int
    expires_at: int


class SignedTagCursorCodec:
    """HMAC-SHA-256 cursor with the same secret, format and 24 hour lifetime as Circle cursors."""

    def __init__(
        self,
        secret: bytes,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        if len(secret) < MINIMUM_SECRET_BYTES:
            raise ValueError(f"cursor signing secret must be at least {MINIMUM_SECRET_BYTES} bytes")
        self._secret = secret
        self._clock = clock or (lambda: datetime.now(UTC))

    @classmethod
    def from_environment(cls) -> "SignedTagCursorCodec":
        return cls(load_cursor_signing_secret())

    def encode(self, *, last_display_order: int, last_tag_id: UUID) -> str:
        now = self._clock()
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("cursor clock must return a timezone-aware datetime")
        issued_at = int(now.timestamp())
        payload = TagCursorPayload(
            version=TAG_CURSOR_VERSION,
            resource="tags",
            last_display_order=last_display_order,
            last_tag_id=last_tag_id,
            issued_at=issued_at,
            expires_at=issued_at + CURSOR_TTL_SECONDS,
        )
        serialized = json.dumps(
            payload.model_dump(mode="json"),
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        encoded_payload = _encode_base64url(serialized)
        signature = hmac.new(
            self._secret,
            encoded_payload.encode("ascii"),
            hashlib.sha256,
        ).digest()
        return f"{encoded_payload}.{_encode_base64url(signature)}"

    def decode(self, cursor: str) -> TagCursorPayload:
        try:
            encoded_payload, encoded_signature = cursor.split(".")
            signature = _decode_base64url(encoded_signature)
            expected_signature = hmac.new(
                self._secret,
                encoded_payload.encode("ascii"),
                hashlib.sha256,
            ).digest()
            if not hmac.compare_digest(signature, expected_signature):
                raise ValueError("signature mismatch")

            serialized = _decode_base64url(encoded_payload)
            raw_payload: Any = json.loads(serialized.decode("utf-8"))
            payload = TagCursorPayload.model_validate(raw_payload)

            now = self._clock()
            if now.tzinfo is None or now.utcoffset() is None:
                raise ValueError("cursor clock must return a timezone-aware datetime")
            now_epoch = int(now.timestamp())
            if payload.issued_at > now_epoch:
                raise ValueError("cursor issued in the future")
            if payload.expires_at - payload.issued_at != CURSOR_TTL_SECONDS:
                raise ValueError("invalid cursor lifetime")
            if now_epoch >= payload.expires_at:
                raise ValueError("cursor expired")
            return payload
        except (ValueError, UnicodeError, json.JSONDecodeError, ValidationError) as error:
            raise InvalidCursorError() from error
