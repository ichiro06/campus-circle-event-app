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

    assert {"/health", "/api/circles", "/api/events", "/api/v1/health"} <= paths.keys()


def test_contract_openapi_contains_only_the_formal_api_surface() -> None:
    schema = build_contract_schema()
    paths = schema["paths"]

    assert set(paths) == {"/api/v1/health"}
    operation = paths["/api/v1/health"]["get"]
    assert operation["operationId"] == "getApiV1Health"
    assert operation["responses"]["200"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/SuccessResponse_ApiHealth_"
    }

    for status in ("500", "503"):
        content = operation["responses"][status]["content"]
        assert set(content) == {PROBLEM_MEDIA_TYPE}
        problem_schema = content[PROBLEM_MEDIA_TYPE]["schema"]
        assert "requestId" in problem_schema["properties"]
        assert "errors" in problem_schema["properties"]
        assert "$defs" not in problem_schema
        assert "$ref" not in json.dumps(problem_schema)


def test_committed_openapi_snapshot_is_current() -> None:
    assert OPENAPI_SNAPSHOT.read_text(encoding="utf-8") == render_openapi_schema()
