import base64
import hashlib
import hmac
import json
from datetime import UTC, datetime, timedelta
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

import pytest

from api.errors import InvalidCursorError
from app_private.seed_tags import INITIAL_TAGS
from circles.cursor import CURSOR_TTL_SECONDS, SignedCircleCursorCodec
from tags.cursor import SignedTagCursorCodec

TEST_SECRET = b"fixed-test-cursor-secret-32-bytes!"
ISSUED_AT = datetime(2026, 10, 29, 0, 0, tzinfo=UTC)


def _codec(now: datetime = ISSUED_AT) -> SignedTagCursorCodec:
    return SignedTagCursorCodec(TEST_SECRET, clock=lambda: now)


def _raw_cursor(payload: dict[str, object], secret: bytes = TEST_SECRET) -> str:
    serialized = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    encoded = base64.urlsafe_b64encode(serialized).rstrip(b"=").decode()
    signature = hmac.new(secret, encoded.encode(), hashlib.sha256).digest()
    return f"{encoded}.{base64.urlsafe_b64encode(signature).rstrip(b'=').decode()}"


def _payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "version": 1,
        "resource": "tags",
        "lastDisplayOrder": 3,
        "lastTagId": str(uuid4()),
        "issuedAt": int(ISSUED_AT.timestamp()),
        "expiresAt": int(ISSUED_AT.timestamp()) + CURSOR_TTL_SECONDS,
    }
    return payload | overrides


def test_initial_tags_are_the_approved_seven_in_order() -> None:
    assert [tag.name for tag in INITIAL_TAGS] == [
        "初心者歓迎",
        "留学生歓迎",
        "兼サーOK",
        "途中入部歓迎",
        "友達作り",
        "少人数",
        "大会あり",
    ]
    assert [tag.display_order for tag in INITIAL_TAGS] == [1, 2, 3, 4, 5, 6, 7]


def test_initial_tag_identities_are_unique_stable_and_fit_the_columns() -> None:
    for column in ("id", "name", "slug", "display_order"):
        values = [getattr(tag, column) for tag in INITIAL_TAGS]
        assert len(set(values)) == len(INITIAL_TAGS), column
    for tag in INITIAL_TAGS:
        assert tag.id == uuid5(NAMESPACE_URL, f"campus-circle-initial-tag-{tag.slug}")
        assert tag.id.version == 5
        assert 0 < len(tag.name) <= 80
        assert 0 < len(tag.slug) <= 80
        assert tag.slug.isascii() and tag.slug == tag.slug.lower()


def test_tag_cursor_round_trip_and_canonical_encoding() -> None:
    tag_id = uuid4()
    first = _codec().encode(last_display_order=4, last_tag_id=tag_id)
    second = _codec().encode(last_display_order=4, last_tag_id=tag_id)

    assert first == second
    payload = _codec(ISSUED_AT + timedelta(hours=1)).decode(first)
    assert payload.last_display_order == 4
    assert payload.last_tag_id == tag_id
    assert payload.resource == "tags"


def test_tag_cursor_expires_after_24_hours() -> None:
    cursor = _codec().encode(last_display_order=1, last_tag_id=uuid4())

    _codec(ISSUED_AT + timedelta(seconds=CURSOR_TTL_SECONDS - 1)).decode(cursor)
    with pytest.raises(InvalidCursorError):
        _codec(ISSUED_AT + timedelta(seconds=CURSOR_TTL_SECONDS)).decode(cursor)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda cursor: cursor[:-2] + ("AA" if not cursor.endswith("AA") else "BB"),
        lambda cursor: "x" + cursor,
        lambda cursor: cursor.split(".")[0],
        lambda cursor: cursor + ".extra",
        lambda cursor: "",
    ],
)
def test_tag_cursor_rejects_tampering(mutate) -> None:
    cursor = _codec().encode(last_display_order=1, last_tag_id=uuid4())

    with pytest.raises(InvalidCursorError):
        _codec().decode(mutate(cursor))


@pytest.mark.parametrize(
    "payload",
    [
        _payload(version=2),
        _payload(resource="circles"),
        _payload(lastDisplayOrder=-1),
        _payload(lastDisplayOrder="3"),
        _payload(lastTagId="not-a-uuid"),
        _payload(unexpected=True),
        _payload(expiresAt=int(ISSUED_AT.timestamp()) + 60),
        _payload(issuedAt=int(ISSUED_AT.timestamp()) + 3600),
    ],
)
def test_tag_cursor_rejects_invalid_signed_payloads(payload: dict[str, object]) -> None:
    with pytest.raises(InvalidCursorError):
        _codec().decode(_raw_cursor(payload))


def test_tag_cursor_rejects_a_different_secret() -> None:
    with pytest.raises(InvalidCursorError):
        _codec().decode(_raw_cursor(_payload(), secret=b"another-secret-of-at-least-32-bytes"))


def test_circle_and_tag_cursors_are_not_interchangeable() -> None:
    circle_cursor = SignedCircleCursorCodec(TEST_SECRET, clock=lambda: ISSUED_AT).encode(
        last_published_at=ISSUED_AT,
        last_circle_id=uuid4(),
        filters={"q": None},
    )
    tag_cursor = _codec().encode(last_display_order=1, last_tag_id=uuid4())

    with pytest.raises(InvalidCursorError):
        _codec().decode(circle_cursor)
    with pytest.raises(InvalidCursorError):
        SignedCircleCursorCodec(TEST_SECRET, clock=lambda: ISSUED_AT).decode(tag_cursor)


def test_tag_cursor_secret_must_be_at_least_32_bytes() -> None:
    with pytest.raises(ValueError, match="at least 32 bytes"):
        SignedTagCursorCodec(b"short")


def test_initial_tag_uuid_literals_are_valid() -> None:
    assert all(isinstance(tag.id, UUID) for tag in INITIAL_TAGS)
