import json
from pathlib import Path

from api.errors import PROBLEM_MEDIA_TYPE
from generate_openapi import build_contract_schema, render_openapi_schema
from main import app

OPENAPI_SNAPSHOT = Path(__file__).parents[1] / "openapi.json"


def test_openapi_generation_is_reproducible() -> None:
    first = render_openapi_schema()
    second = render_openapi_schema()

    assert first == second
    assert json.loads(first)["openapi"].startswith("3.")


def test_runtime_openapi_preserves_prototype_paths_and_adds_api_v1() -> None:
    paths = app.openapi()["paths"]

    assert {
        "/health",
        "/api/circles",
        "/api/events",
        "/api/v1/health",
        "/api/v1/circles",
        "/api/v1/circles/{circleId}",
    } <= paths.keys()


def test_contract_openapi_contains_only_the_formal_api_surface() -> None:
    schema = build_contract_schema()
    paths = schema["paths"]

    assert set(paths) == {
        "/api/v1/health",
        "/api/v1/circles",
        "/api/v1/circles/{circleId}",
    }
    health_operation = paths["/api/v1/health"]["get"]
    assert health_operation["operationId"] == "getApiV1Health"
    assert health_operation["responses"]["200"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/SuccessResponse_ApiHealth_"
    }

    for status in ("500", "503"):
        content = health_operation["responses"][status]["content"]
        assert set(content) == {PROBLEM_MEDIA_TYPE}
        problem_schema = content[PROBLEM_MEDIA_TYPE]["schema"]
        assert "requestId" in problem_schema["properties"]
        assert "errors" in problem_schema["properties"]
        assert "$defs" not in problem_schema
        assert "$ref" not in json.dumps(problem_schema)

    list_operation = paths["/api/v1/circles"]["get"]
    assert list_operation["operationId"] == "listPublicCircles"
    assert [parameter["name"] for parameter in list_operation["parameters"]] == [
        "q",
        "officialStatus",
        "circleType",
        "campFrequencyCode",
        "memberCountBand",
        "activityFrequencyCode",
        "weekday",
        "timeBand",
        "tagId",
        "genderBalanceCode",
        "sort",
        "cursor",
        "limit",
    ]
    assert list_operation["responses"]["200"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/CircleCollectionResponse"
    }
    for status in ("400", "422", "500", "503"):
        assert set(list_operation["responses"][status]["content"]) == {PROBLEM_MEDIA_TYPE}
    invalid_cursor_contract = list_operation["responses"]["400"]["content"][PROBLEM_MEDIA_TYPE]
    assert invalid_cursor_contract["example"]["code"] == "INVALID_CURSOR"

    detail_operation = paths["/api/v1/circles/{circleId}"]["get"]
    assert detail_operation["operationId"] == "getPublicCircle"
    assert detail_operation["parameters"] == [
        {
            "name": "circleId",
            "in": "path",
            "required": True,
            "schema": {"type": "string", "format": "uuid", "title": "Circleid"},
        }
    ]
    assert detail_operation["responses"]["200"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/SuccessResponse_CircleDetail_"
    }
    for status in ("404", "422", "500", "503"):
        assert set(detail_operation["responses"][status]["content"]) == {PROBLEM_MEDIA_TYPE}

    page_schema = schema["components"]["schemas"]["CirclePageMetadata"]
    assert "totalCount" in page_schema["required"]
    assert "/api/circles" not in paths
    assert "/api/events" not in paths


def test_runtime_formal_subset_matches_the_contract_schema() -> None:
    contract = build_contract_schema()
    runtime = app.openapi()

    assert {path: runtime["paths"][path] for path in contract["paths"]} == contract["paths"]
    contract_schemas = contract["components"]["schemas"]
    assert {
        name: runtime["components"]["schemas"][name] for name in contract_schemas
    } == contract_schemas


def test_committed_openapi_snapshot_is_current() -> None:
    assert OPENAPI_SNAPSHOT.read_text(encoding="utf-8") == render_openapi_schema()
