import base64
import binascii
import hashlib
import hmac
import json
import os
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import ValidationError

from api.errors import InvalidCursorError
from api.models import ApiModel, UtcDateTime

CURSOR_SECRET_ENV = "CURSOR_SIGNING_SECRET"
CURSOR_TTL_SECONDS = 24 * 60 * 60
CURSOR_VERSION = 1
MINIMUM_SECRET_BYTES = 32


class CircleCursorPayload(ApiModel):
    version: Literal[1]
    sort: Literal["newest"]
    last_published_at: UtcDateTime | None
    last_circle_id: UUID
    filters: dict[str, str | list[str] | None]
    issued_at: int
    expires_at: int


def load_cursor_signing_secret() -> bytes:
    raw_secret = os.getenv(CURSOR_SECRET_ENV)
    if raw_secret is None or not raw_secret:
        raise RuntimeError(f"{CURSOR_SECRET_ENV} must be configured")
    secret = raw_secret.encode("utf-8")
    if len(secret) < MINIMUM_SECRET_BYTES:
        raise RuntimeError(f"{CURSOR_SECRET_ENV} must be at least {MINIMUM_SECRET_BYTES} bytes")
    return secret


def _encode_base64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _decode_base64url(value: str) -> bytes:
    if not value or "=" in value:
        raise ValueError("invalid base64url")
    padding = "=" * (-len(value) % 4)
    decoded = base64.b64decode(
        value + padding,
        altchars=b"-_",
        validate=True,
    )
    if _encode_base64url(decoded) != value:
        raise ValueError("non-canonical base64url")
    return decoded


class SignedCircleCursorCodec:
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
    def from_environment(cls) -> "SignedCircleCursorCodec":
        return cls(load_cursor_signing_secret())

    def encode(
        self,
        *,
        last_published_at: datetime | None,
        last_circle_id: UUID,
        filters: dict[str, str | list[str] | None],
    ) -> str:
        now = self._clock()
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("cursor clock must return a timezone-aware datetime")
        issued_at = int(now.timestamp())
        payload = CircleCursorPayload(
            version=CURSOR_VERSION,
            sort="newest",
            last_published_at=last_published_at,
            last_circle_id=last_circle_id,
            filters=filters,
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

    def decode(self, cursor: str) -> CircleCursorPayload:
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
            payload = CircleCursorPayload.model_validate(raw_payload)

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
        except (
            ValueError,
            UnicodeError,
            json.JSONDecodeError,
            ValidationError,
            binascii.Error,
        ) as error:
            raise InvalidCursorError() from error
