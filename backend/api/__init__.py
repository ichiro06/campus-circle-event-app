from fastapi import FastAPI

from api.errors import install_exception_handlers
from api.request_id import RequestIdMiddleware


def install_api_foundation(app: FastAPI) -> None:
    """Install the shared request context and error contract for formal APIs."""

    app.add_middleware(RequestIdMiddleware)
    install_exception_handlers(app)
