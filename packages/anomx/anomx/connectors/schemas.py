"""Pandera validation schemas for connectors."""

from __future__ import annotations

import pandera.polars as pa
import polars as pl


def build_timeseries_schema(timestamp_column: str, value_column: str) -> pa.DataFrameSchema:
    """Build a schema for univariate time-series batch files."""
    return pa.DataFrameSchema(
        {
            timestamp_column: pa.Column(pl.Datetime(time_unit="us", time_zone="UTC"), nullable=False),
            value_column: pa.Column(pl.Float64, nullable=False),
        },
        strict=False,
        coerce=True,
    )
