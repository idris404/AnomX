"""Tests for CsvBatchSource."""

from datetime import UTC, datetime
from pathlib import Path

import polars as pl
import pytest
from pandera.errors import SchemaError

from anomx.connectors.csv_batch import CsvBatchSource


def _write_csv(path: Path, rows: list[tuple[str, float]]) -> None:
    frame = pl.DataFrame(
        {
            "timestamp": [datetime.fromisoformat(ts).replace(tzinfo=UTC) for ts, _ in rows],
            "value": [value for _, value in rows],
        }
    )
    frame.write_csv(path)


def test_csv_batch_source_reads_valid_file(tmp_path: Path) -> None:
    csv_path = tmp_path / "sample.csv"
    _write_csv(
        csv_path,
        [
            ("2024-01-01T00:00:00", 1.0),
            ("2024-01-01T00:01:00", 2.5),
        ],
    )

    source = CsvBatchSource(
        path=csv_path,
        timestamp_column="timestamp",
        value_column="value",
    )
    records = source.read()

    assert len(records) == 2
    assert records[0]["payload"]["value"] == 1.0
    assert records[0]["observed_at"].tzinfo is not None


def test_csv_batch_source_rejects_invalid_values(tmp_path: Path) -> None:
    csv_path = tmp_path / "invalid.csv"
    pl.DataFrame(
        {
            "timestamp": [datetime(2024, 1, 1, tzinfo=UTC)],
            "value": ["not-a-number"],
        }
    ).write_csv(csv_path)

    source = CsvBatchSource(
        path=csv_path,
        timestamp_column="timestamp",
        value_column="value",
    )

    with pytest.raises((SchemaError, pl.exceptions.InvalidOperationError, ValueError)):
        source.read()
