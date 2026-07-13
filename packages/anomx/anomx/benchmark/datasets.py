"""Benchmark dataset builders."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

import polars as pl

from anomx.benchmark.injector import AnomalyInjector, generate_baseline_series
from anomx.benchmark.models import BenchmarkConfig, CsvDatasetConfig, SyntheticDatasetConfig


@dataclass
class BenchmarkDataset:
    records: list[dict[str, Any]]
    ground_truth: set[int]
    duration_hours: float


def build_dataset(config: BenchmarkConfig) -> BenchmarkDataset:
    if isinstance(config.dataset, SyntheticDatasetConfig):
        return _build_synthetic_dataset(config.dataset, config.seed)
    return _build_csv_dataset(config.dataset)


def _build_synthetic_dataset(config: SyntheticDatasetConfig, seed: int) -> BenchmarkDataset:
    baseline = generate_baseline_series(config.n_samples, config.base_value, seed)
    injector = AnomalyInjector(seed=seed + 1)
    values, anomaly_indices, _ = injector.inject(
        baseline,
        n_anomalies=config.n_anomalies,
        kinds=config.anomaly_types,
    )

    start = datetime(2024, 1, 1, tzinfo=UTC)
    records: list[dict[str, Any]] = []
    for index, value in enumerate(values):
        records.append(
            {
                "index": index,
                "observation_id": index,
                "observed_at": start + timedelta(seconds=config.interval_seconds * index),
                "value": value,
            }
        )

    duration_hours = (config.n_samples * config.interval_seconds) / 3600.0
    return BenchmarkDataset(records=records, ground_truth=anomaly_indices, duration_hours=duration_hours)


def _build_csv_dataset(config: CsvDatasetConfig) -> BenchmarkDataset:
    if not config.path.exists():
        msg = f"Benchmark CSV not found: {config.path}"
        raise FileNotFoundError(msg)

    frame = pl.read_csv(config.path, try_parse_dates=True)
    records: list[dict[str, Any]] = []
    ground_truth: set[int] = set()

    for index, row in enumerate(frame.iter_rows(named=True)):
        is_anomaly = bool(int(row[config.label_column]))
        if is_anomaly:
            ground_truth.add(index)
        records.append(
            {
                "index": index,
                "observation_id": index,
                "observed_at": row[config.timestamp_column],
                "value": float(row[config.value_column]),
            }
        )

    duration_hours = (len(records) * config.interval_seconds) / 3600.0
    return BenchmarkDataset(records=records, ground_truth=ground_truth, duration_hours=duration_hours)
