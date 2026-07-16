"""Unit tests for Postgres query connector."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import psycopg
import pytest

from anomx.config.models import CsvBatchSourceConfig, DatabaseSettings
from anomx.connectors.postgres_query import PostgresQuerySource
from anomx.ingest.service import IngestService
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
def test_postgres_query_source_reads_aggregate(require_postgres: str, tmp_path: Path) -> None:
    stream_name = f"test_pg_query_{uuid4().hex[:8]}"
    csv_path = tmp_path / "seed.csv"
    generate_timeseries_csv(csv_path, rows=50, anomaly_count=5)

    settings = DatabaseSettings()
    source_config = CsvBatchSourceConfig(
        name=stream_name,
        source_type="csv_batch",
        path=Path(csv_path),
        timestamp_column="timestamp",
        value_column="value",
    )

    try:
        IngestService(database=settings).ingest(source_config)

        query = f"""
            SELECT
                date_trunc('hour', o.observed_at) AS observed_at,
                avg((o.payload->>'value')::double precision) AS value
            FROM observations o
            JOIN streams s ON s.id = o.stream_id
            WHERE s.name = '{stream_name}'
            GROUP BY 1
            ORDER BY 1
        """
        source = PostgresQuerySource(
            database=settings,
            query=query,
            timestamp_column="observed_at",
            value_column="value",
        )
        records = source.read()

        assert records
        assert records[0]["observed_at"].tzinfo is not None
        assert "value" in records[0]["payload"]
    finally:
        with psycopg.connect(require_postgres) as connection:
            cleanup_stream(connection, stream_name)
