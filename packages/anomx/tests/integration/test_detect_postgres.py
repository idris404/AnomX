"""Integration test for detect pipeline against PostgreSQL."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import psycopg
import pytest

from anomx.config.detect_models import DetectConfig, DetectorConfig
from anomx.config.loader import load_detect_config
from anomx.config.models import CsvBatchSourceConfig, DatabaseSettings
from anomx.detect.service import DetectService
from anomx.ingest.service import IngestService
from anomx.storage.detection import DetectionRepository
from anomx.storage.postgres import postgres_connection
from tests.helpers import cleanup_stream, generate_timeseries_csv


@pytest.mark.integration
def test_detect_after_ingest(require_postgres: str, tmp_path: Path) -> None:
    stream_name = f"test_detect_{uuid4().hex[:8]}"
    csv_path = tmp_path / "detect_me.csv"
    generate_timeseries_csv(csv_path, rows=500, anomaly_count=25)

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
        ingest_result = IngestService(database=settings).ingest_csv_batch(source_config)
        assert ingest_result.records_written == 500

        detect_result = DetectService(database=settings).detect_stream(stream_name, detect_config)
        assert detect_result.observations_scored == 500
        assert detect_result.alerts_created > 0

        with postgres_connection(settings.dsn) as connection:
            repository = DetectionRepository(connection)
            assert repository.count_alerts_for_run(detect_result.run_id) == detect_result.alerts_created
    finally:
        with psycopg.connect(require_postgres) as connection:
            cleanup_stream(connection, stream_name)


def test_load_default_detector_config() -> None:
    config = load_detect_config(Path("config/detectors.yaml"))
    assert len(config.detectors) == 2
    assert config.detectors[0].type == "mad"
