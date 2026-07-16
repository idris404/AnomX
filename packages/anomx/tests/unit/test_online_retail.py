"""Tests for Online Retail batch connector."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import polars as pl

from anomx.connectors.online_retail import OnlineRetailBatchSource


def test_online_retail_aggregates_daily_revenue(tmp_path: Path) -> None:
    csv_path = tmp_path / "retail.csv"
    day = datetime(2011, 1, 1, tzinfo=UTC)
    next_day = day + timedelta(days=1)
    pl.DataFrame(
        {
            "InvoiceDate": [day, day, next_day],
            "Quantity": [2.0, 1.0, 5.0],
            "UnitPrice": [10.0, 4.0, 2.0],
        }
    ).write_csv(csv_path)

    source = OnlineRetailBatchSource(path=csv_path, aggregate="daily_revenue")
    records = source.read()

    assert len(records) == 2
    assert records[0]["payload"]["value"] == 24.0
    assert records[1]["payload"]["value"] == 10.0
