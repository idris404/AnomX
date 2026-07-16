"""Tests for NAB batch connector."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import polars as pl

from anomx.connectors.nab_batch import NabBatchSource


def test_nab_batch_source_attaches_labels(tmp_path: Path) -> None:
    csv_path = tmp_path / "series.csv"
    pl.DataFrame(
        {
            "timestamp": [
                datetime(2014, 7, 4, 18, 0, tzinfo=UTC),
                datetime(2014, 7, 4, 19, 30, tzinfo=UTC),
                datetime(2014, 7, 5, 2, 0, tzinfo=UTC),
            ],
            "value": [40.0, 90.0, 41.0],
        }
    ).write_csv(csv_path)

    labels_path = tmp_path / "combined_windows.json"
    labels_path.write_text(
        json.dumps(
            {
                "realKnownCause/series.csv": [
                    ["2014-07-04 19:00:00", "2014-07-05 01:00:00"],
                ]
            }
        ),
        encoding="utf-8",
    )

    source = NabBatchSource(
        path=csv_path,
        dataset_name="series",
        labels_path=labels_path,
        labels_key="realKnownCause/series.csv",
    )
    records = source.read()

    assert len(records) == 3
    assert records[0]["payload"]["label"] == 0
    assert records[1]["payload"]["label"] == 1
    assert records[2]["payload"]["label"] == 0
    assert records[0]["payload"]["dataset"] == "series"
