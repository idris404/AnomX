"""Integration tests for batch ingestion against PostgreSQL."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import psycopg
import pytest

from anomx.config.models import CsvBatchSourceConfig, DatabaseSettings
from anomx.ingest.service import IngestService
from anomx.storage.ingestion import IngestionRepository
from anomx.storage.postgres import postgres_connection
from tests.helpers import cleanup_stream, generate_timeseries_csv


@pytest.mark.integration
def test_ingest_10k_rows_idempotent(require_postgres: str, tmp_path: Path) -> None:
    stream_name = f"test_ingest_{uuid4().hex[:8]}"
    csv_path = tmp_path / "ten_k.csv"
    generate_timeseries_csv(csv_path, rows=10_000)

    config = CsvBatchSourceConfig(
        name=stream_name,
        source_type="csv_batch",
        path=csv_path,
        timestamp_column="timestamp",
        value_column="value",
    )
    settings = DatabaseSettings()
    service = IngestService(database=settings)

    try:
        first = service.ingest_csv_batch(config)
        assert first.skipped is False
        assert first.records_read == 10_000
        assert first.records_written == 10_000

        with postgres_connection(settings.dsn) as connection:
            repository = IngestionRepository(connection)
            assert repository.count_observations_for_run(first.run_id) == 10_000
            assert repository.count_observations_for_stream(first.stream_id) == 10_000

        second = service.ingest_csv_batch(config)
        assert second.skipped is True
        assert second.run_id == first.run_id
        assert second.records_written == 0

        with postgres_connection(settings.dsn) as connection:
            repository = IngestionRepository(connection)
            assert repository.count_observations_for_stream(first.stream_id) == 10_000
    finally:
        with psycopg.connect(require_postgres) as connection:
            cleanup_stream(connection, stream_name)
