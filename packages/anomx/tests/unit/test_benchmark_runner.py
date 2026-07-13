"""Benchmark runner reproducibility and report tests."""

from __future__ import annotations

from pathlib import Path

from anomx.benchmark.models import BenchmarkConfig, DetectorConfig, OutputConfig, SyntheticDatasetConfig
from anomx.benchmark.runner import BenchmarkRunner
from anomx.config.loader import load_benchmark_config


def _synthetic_config(tmp_path: Path, seed: int = 42) -> BenchmarkConfig:
    return BenchmarkConfig(
        seed=seed,
        dataset=SyntheticDatasetConfig(n_samples=600, n_anomalies=30),
        detectors=[
            DetectorConfig(name="mad", type="mad", weight=0.5),
            DetectorConfig(name="isolation_forest", type="isolation_forest", weight=0.5),
        ],
        output=OutputConfig(directory=tmp_path, prefix="test_benchmark"),
    )


def test_benchmark_runner_is_reproducible(tmp_path: Path) -> None:
    config = _synthetic_config(tmp_path, seed=123)

    first = BenchmarkRunner(config).run()
    second = BenchmarkRunner(config).run()

    assert first.n_samples == second.n_samples
    assert first.n_anomalies == second.n_anomalies
    for left, right in zip(first.detectors, second.detectors, strict=True):
        assert left.name == right.name
        assert left.precision == right.precision
        assert left.recall == right.recall
        assert left.f1 == right.f1


def test_benchmark_runner_writes_reports(tmp_path: Path) -> None:
    result = BenchmarkRunner(_synthetic_config(tmp_path)).run()

    assert result.report_json.exists()
    assert result.report_markdown.exists()
    markdown = result.report_markdown.read_text(encoding="utf-8")
    assert "# AnomX Benchmark Report" in markdown
    assert "ensemble" in markdown.lower() or "isolation_forest" in markdown


def test_benchmark_meets_phase3_detector_thresholds(tmp_path: Path) -> None:
    config = BenchmarkConfig(
        seed=42,
        dataset=SyntheticDatasetConfig(
            n_samples=1000,
            n_anomalies=50,
            anomaly_types=["point"],
        ),
        detectors=[
            DetectorConfig(name="mad", type="mad", weight=0.5),
            DetectorConfig(name="isolation_forest", type="isolation_forest", weight=0.5),
        ],
        output=OutputConfig(directory=tmp_path, prefix="test_benchmark"),
    )
    result = BenchmarkRunner(config).run()

    for detector in result.detectors:
        assert detector.recall > 0.7, f"{detector.name} recall={detector.recall}"
        assert detector.precision > 0.6, f"{detector.name} precision={detector.precision}"


def test_load_default_benchmark_config() -> None:
    config = load_benchmark_config(Path("config/benchmark.yaml"))
    assert config.seed == 42
    assert config.dataset.type == "synthetic"
    assert len(config.detectors) == 2
