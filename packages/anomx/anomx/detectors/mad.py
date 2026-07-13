"""Robust univariate anomaly detection via MAD (Median Absolute Deviation)."""

from __future__ import annotations

from typing import Any

import structlog

logger = structlog.get_logger(__name__)

_MAD_SCALE = 1.4826


class MADDetector:
    """Robust z-score using MAD — interpretable baseline for univariate series."""

    def __init__(
        self,
        value_key: str = "value",
        eps: float = 1e-9,
        calibration_percentile: float = 95.0,
    ) -> None:
        self._value_key = value_key
        self._eps = eps
        self._calibration_percentile = calibration_percentile
        self._median: float = 0.0
        self._mad: float = 1.0
        self._threshold: float = 0.0

    def fit(self, data: list[dict[str, Any]]) -> None:
        values = [_extract_value(record, self._value_key) for record in data]
        if not values:
            msg = "MADDetector.fit requires at least one observation"
            raise ValueError(msg)

        sorted_values = sorted(values)
        mid = len(sorted_values) // 2
        if len(sorted_values) % 2 == 0:
            self._median = (sorted_values[mid - 1] + sorted_values[mid]) / 2.0
        else:
            self._median = sorted_values[mid]

        deviations = [abs(value - self._median) for value in sorted_values]
        deviations.sort()
        if len(deviations) % 2 == 0:
            raw_mad = (deviations[mid - 1] + deviations[mid]) / 2.0
        else:
            raw_mad = deviations[mid]
        self._mad = max(raw_mad, self._eps)
        fit_scores = [
            abs(value - self._median) / (_MAD_SCALE * self._mad) for value in sorted_values
        ]
        self._threshold = percentile_threshold_inline(fit_scores, self._calibration_percentile)

        logger.debug(
            "mad_fitted",
            median=self._median,
            mad=self._mad,
            threshold=self._threshold,
            n_samples=len(values),
        )

    def score(self, data: list[dict[str, Any]]) -> list[float]:
        return [
            abs(_extract_value(record, self._value_key) - self._median)
            / (_MAD_SCALE * self._mad)
            for record in data
        ]

    def predict(self, data: list[dict[str, Any]]) -> list[bool]:
        scores = self.score(data)
        if not scores:
            return []
        return [score > self._threshold for score in scores]

    @property
    def median(self) -> float:
        return self._median

    @property
    def mad(self) -> float:
        return self._mad

    @property
    def threshold(self) -> float:
        return self._threshold

    @property
    def value_key(self) -> str:
        return self._value_key


def _extract_value(record: dict[str, Any], value_key: str) -> float:
    if value_key not in record:
        msg = f"Missing value key '{value_key}' in observation record"
        raise KeyError(msg)
    return float(record[value_key])


def percentile_threshold_inline(scores: list[float], percentile: float) -> float:
    sorted_scores = sorted(scores)
    index = int((len(sorted_scores) - 1) * percentile / 100.0)
    return sorted_scores[index]
