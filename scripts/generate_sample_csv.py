"""Generate sample CSV files for local development."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import polars as pl


def generate_timeseries_csv(path: Path, rows: int) -> None:
    start = datetime(2024, 1, 1, tzinfo=UTC)
    timestamps = [start + timedelta(minutes=index) for index in range(rows)]
    values = [float(20 + (index % 50) * 0.1) for index in range(rows)]
    frame = pl.DataFrame({"timestamp": timestamps, "value": values})
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.write_csv(path)


def main() -> None:
    output = Path("data/samples/example.csv")
    generate_timeseries_csv(output, rows=100)
    print(f"Wrote 100 rows to {output}")  # noqa: T201


if __name__ == "__main__":
    main()
