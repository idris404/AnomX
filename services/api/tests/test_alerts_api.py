"""Integration tests for alert API routes."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import psycopg
import pytest
from fastapi.testclient import TestClient

from anomx.config.detect_models import DetectConfig, DetectorConfig
from anomx.config.models import CsvBatchSourceConfig, DatabaseSettings
from anomx.detect.service import DetectService
from anomx.ingest.service import IngestService
from app.main import app
from tests.helpers import cleanup_stream, generate_timeseries_csv


@pytest.fixture
def require_postgres() -> str:
    dsn = "postgresql://anomx:anomx@localhost:5433/anomx"
    try:
        with psycopg.connect(dsn) as connection:
            connection.execute("SELECT 1")
    except psycopg.Error:
        pytest.skip("PostgreSQL is not available on localhost:5433")
    return dsn


@pytest.mark.integration
def test_alert_api_lists_and_details(require_postgres: str, tmp_path: Path) -> None:
    stream_name = f"test_api_{uuid4().hex[:8]}"
    csv_path = tmp_path / "api_alerts.csv"
    generate_timeseries_csv(csv_path, rows=300, anomaly_count=20)

    source_config = CsvBatchSourceConfig(
        name=stream_name,
        source_type="csv_batch",
        path=csv_path,
        timestamp_column="timestamp",
        value_column="value",
    )
    settings = DatabaseSettings()
    detect_config = DetectConfig(
        detectors=[
            DetectorConfig(name="mad", type="mad", weight=0.5),
            DetectorConfig(name="isolation_forest", type="isolation_forest", weight=0.5),
        ]
    )

    client = TestClient(app)

    try:
        IngestService(database=settings).ingest_csv_batch(source_config)
        DetectService(database=settings).detect_stream(stream_name, detect_config)

        streams_response = client.get("/streams")
        assert streams_response.status_code == 200
        stream_names = [item["name"] for item in streams_response.json()["streams"]]
        assert stream_name in stream_names

        alerts_response = client.get(f"/streams/{stream_name}/alerts?limit=5")
        assert alerts_response.status_code == 200
        alerts_payload = alerts_response.json()
        assert alerts_payload["stream"] == stream_name
        assert alerts_payload["alerts"]
        first = alerts_payload["alerts"][0]
        assert first["summary"]
        assert first["rules"]

        detail_response = client.get(f"/alerts/{first['alert_id']}")
        assert detail_response.status_code == 200
        detail = detail_response.json()["alert"]
        assert detail["detectors"]
        assert detail["feature_contributions"]
    finally:
        with psycopg.connect(require_postgres) as connection:
            cleanup_stream(connection, stream_name)
