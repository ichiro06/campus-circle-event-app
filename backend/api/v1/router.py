from fastapi import APIRouter, Request

from api.errors import openapi_problem_response
from api.models import ApiHealth, RequestMetadata, SuccessResponse
from api.request_id import get_request_id

router = APIRouter(prefix="/api/v1", tags=["API v1"])


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
