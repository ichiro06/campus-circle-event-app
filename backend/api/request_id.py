from contextvars import ContextVar
from uuid import UUID, uuid4

from starlette.requests import Request
from starlette.types import ASGIApp, Receive, Scope, Send

_current_request_id: ContextVar[UUID | None] = ContextVar(
    "current_request_id",
    default=None,
)


class RequestIdMiddleware:
    """Assign a server-generated UUID to each HTTP request lifecycle."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = uuid4()
        scope.setdefault("state", {})["request_id"] = request_id
        token = _current_request_id.set(request_id)
        try:
            await self.app(scope, receive, send)
        finally:
            _current_request_id.reset(token)


def get_request_id(request: Request) -> UUID:
    request_id = getattr(request.state, "request_id", None)
    if isinstance(request_id, UUID):
        return request_id

    request_id = uuid4()
    request.state.request_id = request_id
    return request_id


def current_request_id() -> UUID | None:
    """Expose the request ID to logging and later service-layer integrations."""

    return _current_request_id.get()
