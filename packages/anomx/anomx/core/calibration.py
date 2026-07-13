"""Threshold calibration utilities (Phase 0 stub)."""

from __future__ import annotations


def percentile_threshold(scores: list[float], percentile: float = 95.0) -> float:
    """Return a threshold at the given percentile of anomaly scores."""
    if not scores:
        msg = "scores must not be empty"
        raise ValueError(msg)
    if not 0.0 < percentile < 100.0:
        msg = "percentile must be between 0 and 100 exclusive"
        raise ValueError(msg)

    sorted_scores = sorted(scores)
    index = int((len(sorted_scores) - 1) * percentile / 100.0)
    return sorted_scores[index]
