from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query, Request
from sqlalchemy.orm import Session

from api.errors import openapi_problem_response
from api.models import ApiHealth, RequestMetadata, SuccessResponse
from api.request_id import get_request_id
from circles.schemas import (
    CircleCollectionResponse,
    CircleDetail,
    CircleListQuery,
)
from circles.service import CircleReadService, build_circle_read_service
from database import get_db

router = APIRouter(prefix="/api/v1", tags=["API v1"])

DatabaseSession = Annotated[Session, Depends(get_db)]
CircleQuery = Annotated[CircleListQuery, Query()]


def get_circle_read_service(db: DatabaseSession) -> CircleReadService:
    return build_circle_read_service(db)


CircleService = Annotated[CircleReadService, Depends(get_circle_read_service)]


@router.get(
    "/health",
    operation_id="getApiV1Health",
    response_model=SuccessResponse[ApiHealth],
    response_model_exclude_none=True,
    responses={
        500: openapi_problem_response("Unexpected server error"),
        503: openapi_problem_response("Service temporarily unavailable"),
    },
    summary="Check the formal API foundation",
)
def api_v1_health(request: Request) -> SuccessResponse[ApiHealth]:
    return SuccessResponse(
        data=ApiHealth(),
        meta=RequestMetadata(request_id=get_request_id(request)),
    )


@router.get(
    "/circles",
    operation_id="listPublicCircles",
    response_model=CircleCollectionResponse,
    responses={
        400: openapi_problem_response(
            "Invalid pagination cursor",
            example={
                "type": "about:blank",
                "title": "Bad Request",
                "status": 400,
                "detail": "The pagination cursor is invalid.",
                "instance": "/api/v1/circles",
                "code": "INVALID_CURSOR",
                "requestId": "00000000-0000-0000-0000-000000000000",
            },
        ),
        422: openapi_problem_response("Request validation failed"),
        500: openapi_problem_response("Unexpected server error"),
        503: openapi_problem_response("Service temporarily unavailable"),
    },
    summary="List public Circles",
)
def list_public_circles(
    request: Request,
    query: CircleQuery,
    service: CircleService,
) -> CircleCollectionResponse:
    result = service.list_public(query)
    return CircleCollectionResponse(
        data=result.data,
        page=result.page,
        meta=RequestMetadata(request_id=get_request_id(request)),
    )


@router.get(
    "/circles/{circleId}",
    operation_id="getPublicCircle",
    response_model=SuccessResponse[CircleDetail],
    responses={
        404: openapi_problem_response("Circle not found"),
        422: openapi_problem_response("Request validation failed"),
        500: openapi_problem_response("Unexpected server error"),
        503: openapi_problem_response("Service temporarily unavailable"),
    },
    summary="Get a public Circle",
)
def get_public_circle(
    request: Request,
    circle_id: Annotated[UUID, Path(alias="circleId")],
    service: CircleService,
) -> SuccessResponse[CircleDetail]:
    return SuccessResponse(
        data=service.get_public(circle_id),
        meta=RequestMetadata(request_id=get_request_id(request)),
    )
