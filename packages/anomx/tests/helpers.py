"""Test helpers."""

from __future__ import annotations

import random
from datetime import UTC, datetime, timedelta
from pathlib import Path

import polars as pl
import psycopg


def generate_timeseries_csv(path: Path, rows: int, *, anomaly_count: int = 0, seed: int = 42) -> None:
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


def generate_labeled_records(
    n: int = 1000,
    n_anomalies: int = 50,
    seed: int = 42,
) -> tuple[list[dict[str, float | int]], set[int]]:
    rng = random.Random(seed)
    anomaly_indices = set(rng.sample(range(n), n_anomalies))
    records: list[dict[str, float | int]] = []

    for index in range(n):
        value = 20.0 + rng.gauss(0, 0.5)
        if index in anomaly_indices:
            value += rng.choice([-1, 1]) * rng.uniform(20, 40)
        records.append({"observation_id": index, "value": value})

    return records, anomaly_indices


def precision_recall(ground_truth: set[int], predicted: set[int]) -> tuple[float, float]:
    if not predicted:
        return 0.0, 0.0
    if not ground_truth:
        return 0.0, 1.0

    true_positive = len(ground_truth & predicted)
    precision = true_positive / len(predicted)
    recall = true_positive / len(ground_truth)
    return precision, recall


def predicted_indices(flags: list[bool]) -> set[int]:
    return {index for index, flag in enumerate(flags) if flag}


def cleanup_stream(connection: psycopg.Connection, stream_name: str) -> None:
    connection.execute("DELETE FROM streams WHERE name = %s", (stream_name,))
    connection.commit()
