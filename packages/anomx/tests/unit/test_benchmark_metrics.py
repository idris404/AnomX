"""Tests for benchmark metrics."""

from anomx.benchmark.metrics import (
    ClassificationCounts,
    classification_counts,
    false_positives_per_hour,
    precision_recall_f1,
)


def test_classification_counts_and_f1() -> None:
    ground_truth = {1, 2, 3, 4, 5}
    predicted = {3, 4, 5, 6, 7}
    counts = classification_counts(ground_truth, predicted)

    assert counts == ClassificationCounts(true_positives=3, false_positives=2, false_negatives=2)
    precision, recall, f1 = precision_recall_f1(counts)
    assert precision == 0.6
    assert recall == 0.6
    assert round(f1, 4) == 0.6


def test_false_positives_per_hour() -> None:
    assert false_positives_per_hour(12, 6.0) == 2.0
