"""Detection quality and latency metrics."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

from anomx.benchmark.models import DetectorBenchmarkResult, LatencyMetrics
from anomx.core.interfaces import Detector


@dataclass(frozen=True)
class ClassificationCounts:
    true_positives: int
    false_positives: int
    false_negatives: int


def classification_counts(ground_truth: set[int], predicted: set[int]) -> ClassificationCounts:
    true_positives = len(ground_truth & predicted)
    false_positives = len(predicted - ground_truth)
    false_negatives = len(ground_truth - predicted)
    return ClassificationCounts(
        true_positives=true_positives,
        false_positives=false_positives,
        false_negatives=false_negatives,
    )


def precision_recall_f1(counts: ClassificationCounts) -> tuple[float, float, float]:
    precision = (
        counts.true_positives / (counts.true_positives + counts.false_positives)
        if counts.true_positives + counts.false_positives
        else 0.0
    )
    recall = (
        counts.true_positives / (counts.true_positives + counts.false_negatives)
        if counts.true_positives + counts.false_negatives
        else 0.0
    )
    if precision + recall == 0:
        return precision, recall, 0.0
    f1 = 2 * precision * recall / (precision + recall)
    return precision, recall, f1


def false_positives_per_hour(false_positives: int, duration_hours: float) -> float:
    if duration_hours <= 0:
        return 0.0
    return false_positives / duration_hours


def predicted_indices(flags: list[bool]) -> set[int]:
    return {index for index, flag in enumerate(flags) if flag}


def evaluate_detector(
    name: str,
    detector: Detector,
    fit_data: list[dict[str, Any]],
    eval_data: list[dict[str, Any]],
    ground_truth: set[int],
    duration_hours: float,
) -> DetectorBenchmarkResult:
    fit_start = time.perf_counter()
    detector.fit(fit_data)
    fit_ms = (time.perf_counter() - fit_start) * 1000

    predict_start = time.perf_counter()
    flags = detector.predict(eval_data)
    predict_ms = (time.perf_counter() - predict_start) * 1000

    counts = classification_counts(ground_truth, predicted_indices(flags))
    precision, recall, f1 = precision_recall_f1(counts)

    return DetectorBenchmarkResult(
        name=name,
        precision=round(precision, 4),
        recall=round(recall, 4),
        f1=round(f1, 4),
        true_positives=counts.true_positives,
        false_positives=counts.false_positives,
        false_negatives=counts.false_negatives,
        false_positives_per_hour=round(
            false_positives_per_hour(counts.false_positives, duration_hours),
            4,
        ),
        latency=LatencyMetrics(
            fit_ms=round(fit_ms, 3),
            predict_ms=round(predict_ms, 3),
            predict_ms_per_sample=round(predict_ms / len(eval_data), 6) if eval_data else 0.0,
        ),
    )
