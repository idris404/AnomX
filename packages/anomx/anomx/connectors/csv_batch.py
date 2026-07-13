"""CSV/Parquet batch source connector."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

import polars as pl
import structlog

from anomx.connectors.schemas import build_timeseries_schema

logger = structlog.get_logger(__name__)


class CsvBatchSource:
    """Reads and validates a local CSV or Parquet file via Polars."""

    def __init__(
        self,
        path: Path,
        timestamp_column: str,
        value_column: str,
        *,
        file_format: Literal["csv", "parquet"] = "csv",
        include_columns: list[str] | None = None,
    ) -> None:
        self._path = path
        self._timestamp_column = timestamp_column
        self._value_column = value_column
        self._file_format = file_format
        self._include_columns = include_columns

    def read(self) -> list[dict[str, Any]]:
        frame = self._load_frame()
        schema = build_timeseries_schema(self._timestamp_column, self._value_column)
        validated = schema.validate(frame)

        records: list[dict[str, Any]] = []
        for row in validated.iter_rows(named=True):
            observed_at = _coerce_timestamp(row[self._timestamp_column])
            payload = _build_payload(row, self._timestamp_column, self._include_columns)
            records.append({"observed_at": observed_at, "payload": payload})

        logger.info(
            "csv_batch_read_complete",
            path=str(self._path),
            rows=len(records),
        )
        return records

    def _load_frame(self) -> pl.DataFrame:
        if self._file_format == "parquet":
            frame = pl.read_parquet(self._path)
        else:
            frame = pl.read_csv(
                self._path,
                try_parse_dates=True,
                infer_schema_length=10_000,
            )

        if self._timestamp_column not in frame.columns:
            msg = f"Missing timestamp column: {self._timestamp_column}"
            raise ValueError(msg)
        if self._value_column not in frame.columns:
            msg = f"Missing value column: {self._value_column}"
            raise ValueError(msg)

        return frame.with_columns(
            pl.col(self._timestamp_column).cast(pl.Datetime(time_unit="us", time_zone="UTC")),
            pl.col(self._value_column).cast(pl.Float64),
        )


def _coerce_timestamp(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _build_payload(
    row: dict[str, Any],
    timestamp_column: str,
    include_columns: list[str] | None,
) -> dict[str, Any]:
    if include_columns is None:
        return {key: _json_safe(value) for key, value in row.items() if key != timestamp_column}

    payload: dict[str, Any] = {}
    for column in include_columns:
        if column in row and column != timestamp_column:
            payload[column] = _json_safe(row[column])
    return payload


def _json_safe(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat()
    return value
