"""Tests for source connector factory."""

from __future__ import annotations

from pathlib import Path

import pytest

from anomx.config.models import CsvBatchSourceConfig, NabBatchSourceConfig, PostgresQuerySourceConfig
from anomx.connectors.csv_batch import CsvBatchSource
from anomx.connectors.factory import build_source
from anomx.connectors.nab_batch import NabBatchSource
from anomx.config.models import DatabaseSettings


def test_build_source_csv_batch(tmp_path: Path) -> None:
    path = tmp_path / "sample.csv"
    path.write_text("timestamp,value\n2024-01-01T00:00:00+00:00,1.0\n", encoding="utf-8")
    config = CsvBatchSourceConfig(
        name="demo",
        source_type="csv_batch",
        path=path,
        timestamp_column="timestamp",
        value_column="value",
    )
    source = build_source(config)
    assert isinstance(source, CsvBatchSource)


def test_build_source_nab_batch(tmp_path: Path) -> None:
    path = tmp_path / "series.csv"
    path.write_text("timestamp,value\n2024-01-01T00:00:00+00:00,1.0\n", encoding="utf-8")
    config = NabBatchSourceConfig(
        name="nab",
        source_type="nab_batch",
        path=path,
        dataset_name="series",
    )
    source = build_source(config)
    assert isinstance(source, NabBatchSource)


def test_build_source_postgres_requires_database() -> None:
    config = PostgresQuerySourceConfig(
        name="pg",
        source_type="postgres_query",
        query="SELECT now() AS observed_at, 1.0 AS value",
        timestamp_column="observed_at",
        value_column="value",
    )
    with pytest.raises(ValueError, match="database settings"):
        build_source(config)

    source = build_source(config, database=DatabaseSettings())
    assert source is not None
