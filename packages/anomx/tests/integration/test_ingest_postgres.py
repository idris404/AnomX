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


@pytest.mark.integration
def test_ingest_reports_only_rows_inserted_after_deduplication(
    require_postgres: str, tmp_path: Path
) -> None:
    stream_name = f"test_dedupe_{uuid4().hex[:8]}"
    csv_path = tmp_path / "duplicates.csv"
    csv_path.write_text(
        "timestamp,value\n2024-01-01T00:00:00Z,1.0\n2024-01-01T00:00:00Z,1.0\n",
        encoding="utf-8",
    )
    config = CsvBatchSourceConfig(
        name=stream_name,
        source_type="csv_batch",
        path=csv_path,
        timestamp_column="timestamp",
        value_column="value",
    )
    try:
        result = IngestService(database=DatabaseSettings()).ingest(config)
        assert result.records_read == 2
        assert result.records_written == 1
    finally:
        with psycopg.connect(require_postgres) as connection:
            cleanup_stream(connection, stream_name)


@pytest.mark.integration
def test_ingest_records_failed_run_after_sql_error(
    require_postgres: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    stream_name = f"test_failure_{uuid4().hex[:8]}"
    csv_path = tmp_path / "failure.csv"
    generate_timeseries_csv(csv_path, rows=10)
    config = CsvBatchSourceConfig(
        name=stream_name,
        source_type="csv_batch",
        path=csv_path,
        timestamp_column="timestamp",
        value_column="value",
    )

    def fail_insert(repository: IngestionRepository, *args: object) -> int:
        repository._connection.execute("SELECT 1 / 0")
        return 0

    monkeypatch.setattr(IngestionRepository, "insert_observations", fail_insert)
    try:
        with pytest.raises(psycopg.errors.DivisionByZero):
            IngestService(database=DatabaseSettings()).ingest(config)
        with psycopg.connect(require_postgres) as connection:
            row = connection.execute(
                "SELECT r.status, r.metadata FROM runs r "
                "JOIN streams s ON s.id = r.stream_id WHERE s.name = %s",
                (stream_name,),
            ).fetchone()
            assert row is not None
            assert row[0] == "failed"
            assert "division by zero" in row[1]["error"]
    finally:
        with psycopg.connect(require_postgres) as connection:
            cleanup_stream(connection, stream_name)
