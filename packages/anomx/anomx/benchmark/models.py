"""Benchmark configuration and result models."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field

from anomx.config.detect_models import CalibrationConfig, DetectorConfig


class SyntheticDatasetConfig(BaseModel):
    type: Literal["synthetic"] = "synthetic"
    n_samples: int = Field(default=1000, ge=100)
    n_anomalies: int = Field(default=50, ge=1)
    anomaly_types: list[Literal["point", "contextual", "drift"]] = Field(
        default=["point", "contextual", "drift"],
    )
    interval_seconds: int = Field(default=60, ge=1)
    base_value: float = 20.0


class CsvDatasetConfig(BaseModel):
    type: Literal["csv"] = "csv"
    path: Path
    timestamp_column: str = "timestamp"
    value_column: str = "value"
    label_column: str = "label"
    interval_seconds: int = Field(default=60, ge=1)


DatasetConfig = Annotated[
    SyntheticDatasetConfig | CsvDatasetConfig,
    Field(discriminator="type"),
]


class EvaluationConfig(BaseModel):
    fit_ratio: float = Field(default=0.8, gt=0.0, lt=1.0)
    calibration: CalibrationConfig = Field(default_factory=CalibrationConfig)


class OutputConfig(BaseModel):
    directory: Path = Path("reports")
    prefix: str = "benchmark"


class BenchmarkConfig(BaseModel):
    seed: int = 42
    dataset: DatasetConfig = Field(default_factory=SyntheticDatasetConfig)
    evaluation: EvaluationConfig = Field(default_factory=EvaluationConfig)
    detectors: list[DetectorConfig] = Field(min_length=1)
    output: OutputConfig = Field(default_factory=OutputConfig)


class LatencyMetrics(BaseModel):
    fit_ms: float
    predict_ms: float
    predict_ms_per_sample: float


class DetectorBenchmarkResult(BaseModel):
    name: str
    precision: float
    recall: float
    f1: float
    true_positives: int
    false_positives: int
    false_negatives: int
    false_positives_per_hour: float
    latency: LatencyMetrics


class BenchmarkResult(BaseModel):
    seed: int
    dataset_type: str
    n_samples: int
    n_anomalies: int
    fit_samples: int
    duration_hours: float
    detectors: list[DetectorBenchmarkResult]
    generated_at: str
    report_json: Path
    report_markdown: Path

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")
