"""Generate sample CSV files for local development."""

from __future__ import annotations

import random
from datetime import UTC, datetime, timedelta
from pathlib import Path

import polars as pl


def generate_timeseries_csv(
    path: Path,
    rows: int,
    *,
    anomaly_count: int = 0,
    seed: int = 42,
) -> None:
    start = datetime(2024, 1, 1, tzinfo=UTC)
    rng = random.Random(seed)
    anomaly_indices = set(rng.sample(range(rows), min(anomaly_count, rows))) if anomaly_count else set()

    timestamps: list[datetime] = []
    values: list[float] = []
    for index in range(rows):
        timestamps.append(start + timedelta(minutes=index))
        value = 20.0 + (index % 50) * 0.1 + rng.gauss(0, 0.2)
        if index in anomaly_indices:
            value += rng.uniform(30, 50)
        values.append(value)

    frame = pl.DataFrame({"timestamp": timestamps, "value": values})
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.write_csv(path)


def main() -> None:
    output = Path("data/samples/example.csv")
    generate_timeseries_csv(output, rows=200, anomaly_count=10)
    print(f"Wrote 200 rows (10 anomalies) to {output}")  # noqa: T201


if __name__ == "__main__":
    main()
