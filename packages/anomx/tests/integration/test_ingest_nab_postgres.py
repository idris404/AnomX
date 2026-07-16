"""Integration tests for NAB ingestion."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import polars as pl
import psycopg
import pytest

from anomx.config.loader import load_source_config
from anomx.config.models import DatabaseSettings
from anomx.ingest.service import IngestService
from tests.helpers import cleanup_stream


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
def test_ingest_nab_batch(require_postgres: str, tmp_path: Path) -> None:
    stream_name = f"test_nab_{uuid4().hex[:8]}"
    csv_path = tmp_path / "nab.csv"
    pl.DataFrame(
        {
            "timestamp": [datetime(2014, 7, 4, 19, 0, tzinfo=UTC)],
            "value": [88.0],
        }
    ).write_csv(csv_path)

    labels_path = tmp_path / "labels.json"
    labels_path.write_text(
        json.dumps({"realKnownCause/nab.csv": [["2014-07-04 19:00:00", "2014-07-04 20:00:00"]]}),
        encoding="utf-8",
    )

    config_path = tmp_path / "source.yaml"
    config_path.write_text(
        f"""
name: {stream_name}
source_type: nab_batch
path: {csv_path.as_posix()}
dataset_name: nab
labels_path: {labels_path.as_posix()}
labels_key: realKnownCause/nab.csv
timestamp_column: timestamp
value_column: value
""".strip(),
        encoding="utf-8",
    )

    settings = DatabaseSettings()
    try:
        config = load_source_config(config_path)
        result = IngestService(database=settings).ingest(config)
        assert result.records_written == 1
        assert result.skipped is False

        result_repeat = IngestService(database=settings).ingest(config)
        assert result_repeat.skipped is True
    finally:
        with psycopg.connect(require_postgres) as connection:
            cleanup_stream(connection, stream_name)
