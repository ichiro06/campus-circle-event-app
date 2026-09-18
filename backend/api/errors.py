import logging
from collections.abc import Mapping
from dataclasses import dataclass
from http import HTTPStatus
from typing import Any, Final

from fastapi import FastAPI, Request
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, PlainTextResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import Response

from api.models import ProblemDetails, ProblemFieldError, to_camel
from api.request_id import get_request_id

logger = logging.getLogger(__name__)

API_V1_PREFIX: Final = "/api/v1"
PROBLEM_MEDIA_TYPE: Final = "application/problem+json"


@dataclass(frozen=True)
class ProblemDefinition:
    status: int
    detail: str


PROBLEM_CATALOG: Final[dict[str, ProblemDefinition]] = {
    "BAD_REQUEST": ProblemDefinition(400, "The request could not be processed."),
    "UNAUTHORIZED": ProblemDefinition(401, "Authentication is required."),
    "FORBIDDEN": ProblemDefinition(403, "This operation is not permitted."),
    "NOT_FOUND": ProblemDefinition(404, "The requested resource was not found."),
    "CONFLICT": ProblemDefinition(409, "The request conflicts with the current state."),
    "VALIDATION_ERROR": ProblemDefinition(422, "One or more request fields are invalid."),
    "RATE_LIMITED": ProblemDefinition(429, "Too many requests were received."),
    "INTERNAL_SERVER_ERROR": ProblemDefinition(500, "An unexpected error occurred."),
    "SERVICE_UNAVAILABLE": ProblemDefinition(503, "The service is temporarily unavailable."),
    "INVALID_CURSOR": ProblemDefinition(400, "The pagination cursor is invalid."),
    "IDEMPOTENCY_KEY_REQUIRED": ProblemDefinition(400, "An Idempotency-Key is required."),
    "REQUEST_IN_PROGRESS": ProblemDefinition(409, "The same request is already in progress."),
    "IDEMPOTENCY_KEY_REUSED": ProblemDefinition(
        422,
        "The Idempotency-Key was already used with a different request.",
    ),
}

STATUS_PROBLEM_CODES: Final[dict[int, str]] = {
    definition.status: code
    for code, definition in PROBLEM_CATALOG.items()
    if code
    in {
        "BAD_REQUEST",
        "UNAUTHORIZED",
        "FORBIDDEN",
        "NOT_FOUND",
        "CONFLICT",
        "VALIDATION_ERROR",
        "RATE_LIMITED",
        "INTERNAL_SERVER_ERROR",
        "SERVICE_UNAVAILABLE",
    }
}


def problem_type_for(_: str) -> str:
    """Resolve a problem code to its URI reference.

    The official URI base is not decided. RFC 9457's neutral about:blank value
    avoids inventing a production domain; a future decision changes this one
    resolver without spreading URI construction across routers.
    """

    return "about:blank"


def _status_title(status_code: int) -> str:
    try:
        return HTTPStatus(status_code).phrase
    except ValueError:
        return "HTTP Error"


class ApplicationError(Exception):
    def __init__(
        self,
        code: str,
        *,
        detail: str | None = None,
        headers: Mapping[str, str] | None = None,
        errors: list[ProblemFieldError] | None = None,
    ) -> None:
        try:
            definition = PROBLEM_CATALOG[code]
        except KeyError as error:
            raise ValueError(f"Unknown problem code: {code}") from error

        super().__init__(code)
        self.code = code
        self.status_code = definition.status
        self.title = _status_title(definition.status)
        self.detail = detail or definition.detail
        self.headers = dict(headers or {})
        self.errors = errors


class InvalidCursorError(ApplicationError):
    def __init__(self) -> None:
        super().__init__("INVALID_CURSOR")


class IdempotencyKeyRequiredError(ApplicationError):
    def __init__(self) -> None:
        super().__init__("IDEMPOTENCY_KEY_REQUIRED")


class RequestInProgressError(ApplicationError):
    def __init__(self, *, retry_after_seconds: int | None = None) -> None:
        headers = (
            {"Retry-After": str(retry_after_seconds)} if retry_after_seconds is not None else None
        )
        super().__init__("REQUEST_IN_PROGRESS", headers=headers)


class IdempotencyKeyReusedError(ApplicationError):
    def __init__(self) -> None:
        super().__init__("IDEMPOTENCY_KEY_REUSED")


def _is_formal_api(request: Request) -> bool:
    path = request.url.path
    return path == API_V1_PREFIX or path.startswith(f"{API_V1_PREFIX}/")


def _problem_response(
    request: Request,
    *,
    status_code: int,
    code: str,
    detail: str,
    headers: Mapping[str, str] | None = None,
    errors: list[ProblemFieldError] | None = None,
) -> JSONResponse:
    problem = ProblemDetails(
        type=problem_type_for(code),
        title=_status_title(status_code),
        status=status_code,
        detail=detail,
        instance=request.url.path,
        code=code,
        request_id=get_request_id(request),
        errors=errors,
    )
    return JSONResponse(
        status_code=status_code,
        content=problem.model_dump(mode="json", exclude_none=True),
        headers=dict(headers or {}),
        media_type=PROBLEM_MEDIA_TYPE,
    )


def _format_validation_field(location: tuple[Any, ...]) -> str:
    components = list(location)
    if components and components[0] in {"body", "cookie", "header", "path", "query"}:
        components.pop(0)

    field = ""
    for component in components:
        if isinstance(component, int):
            field += f"[{component}]"
            continue
        name = to_camel(str(component))
        field = f"{field}.{name}" if field else name
    return field or "request"


async def application_error_handler(request: Request, error: ApplicationError) -> Response:
    return _problem_response(
        request,
        status_code=error.status_code,
        code=error.code,
        detail=error.detail,
        headers=error.headers,
        errors=error.errors,
    )


async def validation_error_handler(
    request: Request,
    error: RequestValidationError,
) -> Response:
    if not _is_formal_api(request):
        return await request_validation_exception_handler(request, error)

    validation_errors = error.errors()
    field_errors = [
        ProblemFieldError(
            field=(
                "request"
                if item.get("type") == "json_invalid"
                else _format_validation_field(tuple(item.get("loc", ())))
            ),
            code=str(item.get("type", "invalid")),
        )
        for item in validation_errors
    ]
    invalid_json = any(item.get("type") == "json_invalid" for item in validation_errors)
    status_code = 400 if invalid_json else 422
    code = "BAD_REQUEST" if invalid_json else "VALIDATION_ERROR"
    return _problem_response(
        request,
        status_code=status_code,
        code=code,
        detail=PROBLEM_CATALOG[code].detail,
        errors=field_errors,
    )


async def http_error_handler(request: Request, error: StarletteHTTPException) -> Response:
    if not _is_formal_api(request):
        return await http_exception_handler(request, error)

    code = STATUS_PROBLEM_CODES.get(error.status_code, f"HTTP_{error.status_code}")
    definition = PROBLEM_CATALOG.get(code)
    detail = definition.detail if definition else "The request could not be completed."
    return _problem_response(
        request,
        status_code=error.status_code,
        code=code,
        detail=detail,
        headers=error.headers,
    )


async def unexpected_error_handler(request: Request, error: Exception) -> Response:
    if not _is_formal_api(request):
        return PlainTextResponse("Internal Server Error", status_code=500)

    request_id = get_request_id(request)
    logger.error(
        "Unhandled formal API exception",
        extra={
            "request_id": str(request_id),
            "exception_type": type(error).__name__,
        },
    )
    return _problem_response(
        request,
        status_code=500,
        code="INTERNAL_SERVER_ERROR",
        detail=PROBLEM_CATALOG["INTERNAL_SERVER_ERROR"].detail,
    )


def openapi_problem_response(description: str) -> dict[str, Any]:
    schema = ProblemDetails.model_json_schema(mode="serialization")
    definitions = schema.pop("$defs", {})

    def inline_local_definitions(value: Any) -> Any:
        if isinstance(value, list):
            return [inline_local_definitions(item) for item in value]
        if not isinstance(value, dict):
            return value

        reference = value.get("$ref")
        if isinstance(reference, str) and reference.startswith("#/$defs/"):
            definition_name = reference.removeprefix("#/$defs/")
            definition = definitions[definition_name]
            siblings = {key: item for key, item in value.items() if key != "$ref"}
            return inline_local_definitions({**definition, **siblings})

        return {key: inline_local_definitions(item) for key, item in value.items()}

    return {
        "description": description,
        "content": {
            PROBLEM_MEDIA_TYPE: {
                "schema": inline_local_definitions(schema),
            }
        },
    }


def install_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(ApplicationError, application_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_error_handler)
    app.add_exception_handler(Exception, unexpected_error_handler)
