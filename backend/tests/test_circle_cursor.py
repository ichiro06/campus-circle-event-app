import base64
import hashlib
import hmac
import json
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from api.errors import InvalidCursorError
from circles.cursor import (
    CURSOR_SECRET_ENV,
    CURSOR_TTL_SECONDS,
    SignedCircleCursorCodec,
    load_cursor_signing_secret,
)

TEST_SECRET = b"fixed-test-cursor-secret-32-bytes!"
ISSUED_AT = datetime(2026, 9, 19, 0, 0, tzinfo=UTC)
FILTERS = {
    "q": "音楽",
    "officialStatus": ["official"],
    "circleType": [],
    "campFrequencyCode": [],
    "memberCountBand": [],
    "activityFrequencyCode": [],
    "weekday": [],
    "timeBand": [],
    "tagId": [],
    "genderBalanceCode": [],
}


def _signed_raw_cursor(payload: dict[str, object]) -> str:
    serialized = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode()
    encoded = base64.urlsafe_b64encode(serialized).rstrip(b"=").decode()
    signature = hmac.new(TEST_SECRET, encoded.encode(), hashlib.sha256).digest()
    encoded_signature = base64.urlsafe_b64encode(signature).rstrip(b"=").decode()
    return f"{encoded}.{encoded_signature}"


def _codec(now: datetime = ISSUED_AT) -> SignedCircleCursorCodec:
    return SignedCircleCursorCodec(TEST_SECRET, clock=lambda: now)


def test_signed_cursor_round_trip_is_canonical_and_filter_bound() -> None:
    circle_id = uuid4()
    published_at = datetime(2026, 9, 18, 12, 30, tzinfo=UTC)
    first = _codec().encode(
        last_published_at=published_at,
        last_circle_id=circle_id,
        filters=FILTERS,
    )
    second = _codec().encode(
        last_published_at=published_at,
        last_circle_id=circle_id,
        filters=FILTERS,
    )

    assert first == second
    payload = _codec().decode(first)
    assert payload.version == 1
    assert payload.sort == "newest"
    assert payload.last_published_at == published_at
    assert payload.last_circle_id == circle_id
    assert payload.filters == FILTERS
    assert payload.expires_at - payload.issued_at == CURSOR_TTL_SECONDS


@pytest.mark.parametrize(
    "cursor",
    [
        "",
        "one-part",
        "too.many.parts",
        "not_base64!.signature",
        "eyJ2ZXJzaW9uIjoxfQ.invalid_signature",
    ],
)
def test_malformed_or_tampered_cursor_is_rejected(cursor: str) -> None:
    with pytest.raises(InvalidCursorError):
        _codec().decode(cursor)


def test_cursor_tampering_is_rejected_without_exposing_a_reason() -> None:
    cursor = _codec().encode(
        last_published_at=None,
        last_circle_id=uuid4(),
        filters=FILTERS,
    )
    encoded, signature = cursor.split(".")
    replacement = "A" if encoded[-1] != "A" else "B"

    with pytest.raises(InvalidCursorError) as captured:
        _codec().decode(f"{encoded[:-1]}{replacement}.{signature}")

    assert captured.value.detail == "The pagination cursor is invalid."


def test_non_canonical_base64url_signature_is_rejected() -> None:
    cursor = _codec().encode(
        last_published_at=None,
        last_circle_id=uuid4(),
        filters=FILTERS,
    )
    encoded, signature = cursor.split(".")
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
    final_index = alphabet.index(signature[-1])
    alias_index = (final_index & ~3) | ((final_index + 1) & 3)
    non_canonical_signature = f"{signature[:-1]}{alphabet[alias_index]}"

    with pytest.raises(InvalidCursorError):
        _codec().decode(f"{encoded}.{non_canonical_signature}")


def test_cursor_is_valid_before_but_not_at_the_24_hour_boundary() -> None:
    cursor = _codec().encode(
        last_published_at=None,
        last_circle_id=uuid4(),
        filters=FILTERS,
    )

    _codec(ISSUED_AT + timedelta(seconds=CURSOR_TTL_SECONDS - 1)).decode(cursor)
    with pytest.raises(InvalidCursorError):
        _codec(ISSUED_AT + timedelta(seconds=CURSOR_TTL_SECONDS)).decode(cursor)


@pytest.mark.parametrize(
    "payload_update",
    [
        {"version": 2},
        {"sort": "recommended"},
        {"expiresAt": int(ISSUED_AT.timestamp()) + CURSOR_TTL_SECONDS + 1},
        {"issuedAt": int(ISSUED_AT.timestamp()) + 1},
    ],
)
def test_invalid_signed_payloads_are_rejected(payload_update: dict[str, object]) -> None:
    payload: dict[str, object] = {
        "version": 1,
        "sort": "newest",
        "lastPublishedAt": None,
        "lastCircleId": str(UUID(int=1)),
        "filters": FILTERS,
        "issuedAt": int(ISSUED_AT.timestamp()),
        "expiresAt": int(ISSUED_AT.timestamp()) + CURSOR_TTL_SECONDS,
    }
    payload.update(payload_update)

    with pytest.raises(InvalidCursorError):
        _codec().decode(_signed_raw_cursor(payload))


def test_cursor_secret_is_required_and_must_be_long_enough(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(CURSOR_SECRET_ENV, raising=False)
    with pytest.raises(RuntimeError):
        load_cursor_signing_secret()

    monkeypatch.setenv(CURSOR_SECRET_ENV, "too-short")
    with pytest.raises(RuntimeError):
        load_cursor_signing_secret()

    configured = "x" * 32
    monkeypatch.setenv(CURSOR_SECRET_ENV, configured)
    assert load_cursor_signing_secret() == configured.encode()
