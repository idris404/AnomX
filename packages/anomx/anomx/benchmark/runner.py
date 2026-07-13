"""Benchmark execution orchestration."""

from __future__ import annotations

from datetime import UTC, datetime

import structlog

from anomx.benchmark.datasets import build_dataset
from anomx.benchmark.metrics import evaluate_detector
from anomx.benchmark.models import BenchmarkConfig, BenchmarkResult
from anomx.benchmark.report import write_reports
from anomx.core.ensemble import EnsembleDetector
from anomx.detectors.factory import build_detector

logger = structlog.get_logger(__name__)


class BenchmarkRunner:
    """Runs a reproducible detector benchmark and writes JSON/Markdown reports."""

    def __init__(self, config: BenchmarkConfig) -> None:
        self._config = config

    def run(self) -> BenchmarkResult:
        dataset = build_dataset(self._config)
        records = dataset.records
        fit_count = max(int(len(records) * self._config.evaluation.fit_ratio), 10)
        fit_count = min(fit_count, len(records) - 1)
        fit_data = records[:fit_count]

        detector_results = []
        for item in self._config.detectors:
            detector = build_detector(item.type, item.params)
            detector_results.append(
                evaluate_detector(
                    name=item.name,
                    detector=detector,
                    fit_data=fit_data,
                    eval_data=records,
                    ground_truth=dataset.ground_truth,
                    duration_hours=dataset.duration_hours,
                )
            )

        ensemble = EnsembleDetector(
            detectors=[build_detector(item.type, item.params) for item in self._config.detectors],
            names=[item.name for item in self._config.detectors],
            weights=[item.weight for item in self._config.detectors],
            calibration_percentile=self._config.evaluation.calibration.percentile,
        )
        detector_results.append(
            evaluate_detector(
                name="ensemble",
                detector=ensemble,
                fit_data=fit_data,
                eval_data=records,
                ground_truth=dataset.ground_truth,
                duration_hours=dataset.duration_hours,
            )
        )

        generated_at = datetime.now(tz=UTC).isoformat()

        result = BenchmarkResult(
            seed=self._config.seed,
            dataset_type=self._config.dataset.type,
            n_samples=len(records),
            n_anomalies=len(dataset.ground_truth),
            fit_samples=fit_count,
            duration_hours=round(dataset.duration_hours, 4),
            detectors=detector_results,
            generated_at=generated_at,
            report_json=self._config.output.directory / "pending.json",
            report_markdown=self._config.output.directory / "pending.md",
        )

        final = write_reports(
            result,
            self._config.output.directory,
            self._config.output.prefix,
        )

        logger.info(
            "benchmark_complete",
            seed=self._config.seed,
            json_report=str(final.report_json),
            markdown_report=str(final.report_markdown),
        )
        return final
