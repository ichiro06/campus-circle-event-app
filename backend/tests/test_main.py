from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_root_reports_api_ready() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "Campus Circle API is ready"}


def test_openapi_marks_current_read_endpoints_as_technical_surface() -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    assert {"/health", "/api/circles", "/api/events"} <= paths.keys()


def test_openapi_exposes_the_versioned_foundation_without_circle_resources() -> None:
    paths = client.get("/openapi.json").json()["paths"]

    assert "/api/v1/health" in paths
    assert "/api/v1/circles" not in paths
