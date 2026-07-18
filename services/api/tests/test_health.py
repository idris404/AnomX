"""API service tests."""

from fastapi.testclient import TestClient

from app.main import app


def test_health_returns_ok() -> None:
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "anomx-api"
    assert payload["version"] == "0.1.0"


def test_health_ready_reports_dependencies() -> None:
    client = TestClient(app)
    response = client.get("/health/ready")

    assert response.status_code in (200, 503)
    payload = response.json()
    assert payload["service"] == "anomx-api"
    assert payload["status"] in ("ready", "degraded")
    assert "postgres" in payload["checks"]
    assert "redis" in payload["checks"]
    for check in payload["checks"].values():
        assert check["status"] in ("ok", "error")
