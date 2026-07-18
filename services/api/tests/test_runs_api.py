"""API tests for run history and metrics."""

from fastapi.testclient import TestClient

from app.main import app


def test_metrics_endpoint_exposes_prometheus_text() -> None:
    client = TestClient(app)
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "anomx_http_requests_total" in response.text


def test_list_stream_runs_unknown_stream_returns_404() -> None:
    client = TestClient(app)
    response = client.get("/streams/does-not-exist/runs")
    assert response.status_code == 404
