"""Integration tests for alert explanations."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import psycopg
import pytest

from anomx.config.detect_models import DetectConfig, DetectorConfig
from anomx.config.models import CsvBatchSourceConfig, DatabaseSettings
from anomx.detect.service import DetectService
from anomx.explain.service import ExplainService
from anomx.ingest.service import IngestService
from anomx.storage.detection import DetectionRepository
from anomx.storage.postgres import postgres_connection
from tests.helpers import cleanup_stream, generate_timeseries_csv


@pytest.mark.integration
def test_detect_persists_readable_explanations(require_postgres: str, tmp_path: Path) -> None:
    stream_name = f"test_explain_{uuid4().hex[:8]}"
    csv_path = tmp_path / "explain_me.csv"
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

    try:
        IngestService(database=settings).ingest_csv_batch(source_config)
        DetectService(database=settings).detect_stream(stream_name, detect_config)

        views = ExplainService(database=settings).list_alert_explanations(stream_name, limit=5)
        assert views, "Expected at least one alert with explanation"

        first = views[0]
        assert first.summary
        assert len(first.rules) >= 3

        with postgres_connection(settings.dsn) as connection:
            repository = DetectionRepository(connection)
            stream = repository.get_stream_by_name(stream_name)
            assert stream is not None
            alerts = repository.list_alerts_for_stream(stream["id"], limit=1)
            explanation = alerts[0]["explanation"]
            assert isinstance(explanation, dict)
            assert "detectors" in explanation
            assert "feature_contributions" in explanation
    finally:
        with psycopg.connect(require_postgres) as connection:
            cleanup_stream(connection, stream_name)
