"""Shared helpers for batch source connectors."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

import polars as pl

from anomx.connectors.schemas import build_timeseries_schema


def load_timeseries_frame(
    path: Path,
    *,
    timestamp_column: str,
    value_column: str,
    file_format: Literal["csv", "parquet"] = "csv",
) -> pl.DataFrame:
    if file_format == "parquet":
        frame = pl.read_parquet(path)
    else:
        frame = pl.read_csv(
            path,
            try_parse_dates=True,
            infer_schema_length=10_000,
        )

    if timestamp_column not in frame.columns:
        msg = f"Missing timestamp column: {timestamp_column}"
        raise ValueError(msg)
    if value_column not in frame.columns:
        msg = f"Missing value column: {value_column}"
        raise ValueError(msg)

    return frame.with_columns(
        pl.col(timestamp_column).cast(pl.Datetime(time_unit="us", time_zone="UTC")),
        pl.col(value_column).cast(pl.Float64),
    )


def records_from_timeseries_frame(
    frame: pl.DataFrame,
    *,
    timestamp_column: str,
    value_column: str,
    include_columns: list[str] | None = None,
    extra_payload: dict[str, Any] | None = None,
    row_extra: Any | None = None,
) -> list[dict[str, Any]]:
    schema = build_timeseries_schema(timestamp_column, value_column)
    validated = schema.validate(frame)

    records: list[dict[str, Any]] = []
    for row in validated.iter_rows(named=True):
        observed_at = coerce_timestamp(row[timestamp_column])
        payload = build_payload(row, timestamp_column, include_columns)
        if extra_payload:
            payload.update(extra_payload)
        if row_extra is not None:
            extra = row_extra(row, observed_at)
            if extra:
                payload.update(extra)
        records.append({"observed_at": observed_at, "payload": payload})
    return records


def coerce_timestamp(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def build_payload(
    row: dict[str, Any],
    timestamp_column: str,
    include_columns: list[str] | None,
) -> dict[str, Any]:
    if include_columns is None:
        return {key: json_safe(value) for key, value in row.items() if key != timestamp_column}

    payload: dict[str, Any] = {}
    for column in include_columns:
        if column in row and column != timestamp_column:
            payload[column] = json_safe(row[column])
    return payload


def json_safe(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat()
    return value
