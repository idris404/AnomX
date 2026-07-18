"""Integration tests for run history queries."""

from __future__ import annotations

from uuid import uuid4

import pytest

from anomx.config.models import CsvBatchSourceConfig, DatabaseSettings
from anomx.detect.service import DetectService
from anomx.ingest.service import IngestService
from anomx.runs.service import RunService
from tests.helpers import cleanup_stream, generate_timeseries_csv


@pytest.mark.integration
def test_list_runs_for_stream(require_postgres: str, tmp_path) -> None:
    stream_name = f"test_runs_{uuid4().hex[:8]}"
    csv_path = tmp_path / "runs.csv"
    generate_timeseries_csv(csv_path, rows=50)

    config = CsvBatchSourceConfig(
        name=stream_name,
        source_type="csv_batch",
        path=csv_path,
        timestamp_column="timestamp",
        value_column="value",
    )
    settings = DatabaseSettings()
    detect_config_path = tmp_path / "detectors.yaml"
    detect_config_path.write_text(
        "defaults:\n  calibration:\n    method: percentile\n    percentile: 95.0\n"
        "  fit_ratio: 0.8\n  value_key: value\ndetectors:\n"
        "  - name: mad\n    type: mad\n    weight: 1.0\n    params:\n      value_key: value\n",
        encoding="utf-8",
    )

    from anomx.config.loader import load_detect_config

    try:
        IngestService(database=settings).ingest(config)
        DetectService(database=settings).detect_stream(
            stream_name,
            load_detect_config(detect_config_path),
        )

        runs = RunService(database=settings).list_runs_for_stream(stream_name, limit=10)
        assert len(runs) >= 2
        run_types = {run.run_type for run in runs}
        assert "ingestion" in run_types
        assert "detection" in run_types
    finally:
        import psycopg

        with psycopg.connect(require_postgres) as connection:
            cleanup_stream(connection, stream_name)
