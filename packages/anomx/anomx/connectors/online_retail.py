"""Online Retail II batch source connector."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import polars as pl
import structlog

from anomx.connectors.common import coerce_timestamp

logger = structlog.get_logger(__name__)

AggregateMode = Literal["daily_revenue", "daily_quantity"]


class OnlineRetailBatchSource:
    """Aggregates Online Retail II invoices into a univariate daily time series."""

    def __init__(
        self,
        path: Path,
        *,
        timestamp_column: str = "InvoiceDate",
        quantity_column: str = "Quantity",
        price_column: str = "UnitPrice",
        aggregate: AggregateMode = "daily_revenue",
    ) -> None:
        self._path = path
        self._timestamp_column = timestamp_column
        self._quantity_column = quantity_column
        self._price_column = price_column
        self._aggregate = aggregate

    def read(self) -> list[dict[str, Any]]:
        frame = pl.read_csv(
            self._path,
            try_parse_dates=True,
            infer_schema_length=10_000,
        )
        required = {
            self._timestamp_column,
            self._quantity_column,
            self._price_column,
        }
        missing = required - set(frame.columns)
        if missing:
            msg = f"Missing required columns: {sorted(missing)}"
            raise ValueError(msg)

        prepared = frame.with_columns(
            pl.col(self._timestamp_column).cast(pl.Datetime(time_unit="us", time_zone="UTC")),
            pl.col(self._quantity_column).cast(pl.Float64),
            pl.col(self._price_column).cast(pl.Float64),
            (pl.col(self._quantity_column) * pl.col(self._price_column)).alias("line_total"),
            pl.col(self._timestamp_column).dt.truncate("1d").alias("day"),
        )

        if self._aggregate == "daily_quantity":
            aggregated = prepared.group_by("day").agg(
                pl.col(self._quantity_column).sum().alias("value"),
                pl.len().alias("invoice_lines"),
            )
        else:
            aggregated = prepared.group_by("day").agg(
                pl.col("line_total").sum().alias("value"),
                pl.len().alias("invoice_lines"),
            )

        aggregated = aggregated.sort("day").rename({"day": "observed_at"})
        records: list[dict[str, Any]] = []
        for row in aggregated.iter_rows(named=True):
            observed_at = coerce_timestamp(row["observed_at"])
            records.append(
                {
                    "observed_at": observed_at,
                    "payload": {
                        "value": float(row["value"]),
                        "aggregate": self._aggregate,
                        "invoice_lines": int(row["invoice_lines"]),
                    },
                }
            )

        logger.info(
            "online_retail_read_complete",
            path=str(self._path),
            aggregate=self._aggregate,
            rows=len(records),
        )
        return records
