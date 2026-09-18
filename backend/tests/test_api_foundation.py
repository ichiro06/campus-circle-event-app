from datetime import UTC, date, datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import Field, ValidationError

from api import install_api_foundation
from api.errors import (
    ApplicationError,
    IdempotencyKeyRequiredError,
    IdempotencyKeyReusedError,
    InvalidCursorError,
    RequestInProgressError,
)
from api.idempotency import (
    IDEMPOTENCY_KEY_HEADER,
    IdempotencyContext,
    IdempotencyReservation,
    StoredIdempotencyResult,
)
from api.models import (
    ApiModel,
    CollectionResponse,
    PageMetadata,
    RequestMetadata,
    SuccessResponse,
    UtcDateTime,
)
from api.pagination import DEFAULT_PAGE_LIMIT, MAX_PAGE_LIMIT, PaginationParams
from api.request_id import current_request_id
from main import app


class SerializationSample(ApiModel):
    resource_id: UUID
    published_at: UtcDateTime
    activity_date: date


class ValidationPayload(ApiModel):
    annual_cost_min_yen: int = Field(ge=0)


def build_error_test_app() -> tuple[FastAPI, dict[str, UUID | None]]:
    test_app = FastAPI()
    install_api_foundation(test_app)
    captured: dict[str, UUID | None] = {}

    @test_app.post("/api/v1/widgets")
    def validate_widget(_: ValidationPayload) -> dict[str, bool]:
        return {"ok": True}

    @test_app.get("/api/v1/conflict")
    def conflict() -> dict[str, bool]:
        captured["request_id"] = current_request_id()
        raise ApplicationError("CONFLICT")

    @test_app.get("/api/v1/explode")
    def explode() -> dict[str, bool]:
        raise RuntimeError(
            "SELECT secret FROM /private/service; token=do-not-return@example.invalid"
        )

    return test_app, captured


def test_api_v1_health_uses_success_envelope_and_unique_request_ids() -> None:
    client = TestClient(app)

    first = client.get("/api/v1/health")
    second = client.get("/api/v1/health")

    assert first.status_code == 200
    assert first.json()["data"] == {"status": "ok", "apiVersion": "v1"}
    first_request_id = UUID(first.json()["meta"]["requestId"])
    second_request_id = UUID(second.json()["meta"]["requestId"])
    assert first_request_id != second_request_id
    assert "x-request-id" not in first.headers


def test_success_and_collection_models_serialize_the_formal_wire_types() -> None:
    resource_id = uuid4()
    request_id = uuid4()
    sample = SerializationSample(
        resource_id=resource_id,
        published_at=datetime(
            2026,
            9,
            18,
            10,
            30,
            tzinfo=timezone(timedelta(hours=9)),
        ),
        activity_date=date(2026, 9, 19),
    )

    single = SuccessResponse(
        data=sample,
        meta=RequestMetadata(request_id=request_id),
    ).model_dump(mode="json")
    collection = CollectionResponse(
        data=[sample],
        page=PageMetadata(has_more=False, limit=20),
        meta=RequestMetadata(request_id=request_id),
    ).model_dump(mode="json")

    assert single == {
        "data": {
            "resourceId": str(resource_id),
            "publishedAt": "2026-09-18T01:30:00Z",
            "activityDate": "2026-09-19",
        },
        "meta": {"requestId": str(request_id)},
    }
    assert collection["data"] == [single["data"]]
    assert collection["page"] == {"hasMore": False, "limit": 20}


def test_utc_datetime_rejects_naive_values() -> None:
    with pytest.raises(ValidationError):
        SerializationSample(
            resource_id=uuid4(),
            published_at=datetime(2026, 9, 18, 1, 30),
            activity_date=date(2026, 9, 19),
        )


def test_pagination_uses_cursor_limits_and_omits_final_cursor() -> None:
    assert PaginationParams().limit == DEFAULT_PAGE_LIMIT == 20
    assert PaginationParams(limit=MAX_PAGE_LIMIT).limit == 50
    assert PaginationParams(cursor="opaque", limit=1).model_dump() == {
        "cursor": "opaque",
        "limit": 1,
    }

    for invalid_limit in (0, 51):
        with pytest.raises(ValidationError):
            PaginationParams(limit=invalid_limit)

    with pytest.raises(ValidationError):
        PageMetadata(has_more=True, limit=20)


def test_validation_error_is_camel_case_problem_details() -> None:
    test_app, _ = build_error_test_app()
    response = TestClient(test_app).post(
        "/api/v1/widgets",
        json={"annualCostMinYen": -1},
    )

    assert response.status_code == 422
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json() == {
        "type": "about:blank",
        "title": "Unprocessable Content",
        "status": 422,
        "detail": "One or more request fields are invalid.",
        "instance": "/api/v1/widgets",
        "code": "VALIDATION_ERROR",
        "requestId": response.json()["requestId"],
        "errors": [
            {
                "field": "annualCostMinYen",
                "code": "greater_than_equal",
            }
        ],
    }
    UUID(response.json()["requestId"])


def test_invalid_json_is_a_400_problem_details_response() -> None:
    test_app, _ = build_error_test_app()
    response = TestClient(test_app).post(
        "/api/v1/widgets",
        content="{",
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 400
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json()["code"] == "BAD_REQUEST"
    assert response.json()["errors"] == [{"field": "request", "code": "json_invalid"}]


def test_404_is_problem_details_only_for_the_formal_api() -> None:
    client = TestClient(app)

    formal_response = client.get("/api/v1/missing")
    technical_response = client.get("/missing")

    assert formal_response.status_code == 404
    assert formal_response.headers["content-type"] == "application/problem+json"
    assert formal_response.json()["code"] == "NOT_FOUND"
    assert technical_response.status_code == 404
    assert technical_response.headers["content-type"] == "application/json"
    assert technical_response.json() == {"detail": "Not Found"}


def test_application_error_reuses_request_lifecycle_id() -> None:
    test_app, captured = build_error_test_app()
    response = TestClient(test_app).get("/api/v1/conflict")

    assert response.status_code == 409
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json()["code"] == "CONFLICT"
    assert response.json()["requestId"] == str(captured["request_id"])


def test_unexpected_error_does_not_expose_internal_details() -> None:
    test_app, _ = build_error_test_app()
    response = TestClient(test_app, raise_server_exceptions=False).get("/api/v1/explode")

    assert response.status_code == 500
    assert response.headers["content-type"] == "application/problem+json"
    body = response.text
    assert response.json()["code"] == "INTERNAL_SERVER_ERROR"
    assert "SELECT" not in body
    assert "/private/service" not in body
    assert "do-not-return" not in body


@pytest.mark.parametrize(
    ("error", "status", "code"),
    [
        (InvalidCursorError(), 400, "INVALID_CURSOR"),
        (IdempotencyKeyRequiredError(), 400, "IDEMPOTENCY_KEY_REQUIRED"),
        (RequestInProgressError(), 409, "REQUEST_IN_PROGRESS"),
        (IdempotencyKeyReusedError(), 422, "IDEMPOTENCY_KEY_REUSED"),
    ],
)
def test_shared_application_errors_are_machine_readable(
    error: ApplicationError,
    status: int,
    code: str,
) -> None:
    assert error.status_code == status
    assert error.code == code


def test_idempotency_models_define_the_later_service_boundary() -> None:
    context = IdempotencyContext(
        key=uuid4(),
        actor_id=uuid4(),
        endpoint="POST /api/v1/reports",
        payload_hash="sha256-placeholder",
    )
    result = StoredIdempotencyResult(
        status_code=201,
        response_reference="report:placeholder",
    )

    reservation = IdempotencyReservation(replay=True, result=result)

    assert IDEMPOTENCY_KEY_HEADER == "Idempotency-Key"
    assert reservation.model_dump()["result"]["statusCode"] == 201
    assert context.model_dump(mode="json")["actorId"] == str(context.actor_id)
    with pytest.raises(ValidationError):
        IdempotencyReservation(replay=True)


def test_datetime_normalizes_to_utc() -> None:
    sample = SerializationSample(
        resource_id=uuid4(),
        published_at=datetime(2026, 9, 18, 1, 30, tzinfo=UTC),
        activity_date=date(2026, 9, 19),
    )

    assert sample.published_at.tzinfo is UTC
