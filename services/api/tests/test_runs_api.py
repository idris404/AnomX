"""API tests for run history and metrics."""

from fastapi.testclient import TestClient

from app.dependencies import get_run_service
from app.main import app


def test_metrics_endpoint_exposes_prometheus_text() -> None:
    client = TestClient(app)
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "anomx_http_requests_total" in response.text


def test_list_stream_runs_unknown_stream_returns_404() -> None:
    class MissingRunService:
        def list_runs_for_stream(self, stream_name: str, *, limit: int = 20) -> list[object]:
            raise ValueError(f"Stream not found: {stream_name}")

    app.dependency_overrides[get_run_service] = lambda: MissingRunService()
    client = TestClient(app)
    try:
        response = client.get("/streams/does-not-exist/runs")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()
