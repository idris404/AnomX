"""Ensemble detector fusion with score normalization and calibration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import structlog

from anomx.core.calibration import percentile_threshold
from anomx.core.interfaces import Detector

logger = structlog.get_logger(__name__)


@dataclass
class _DetectorState:
    detector: Detector
    name: str
    weight: float
    score_min: float = 0.0
    score_max: float = 1.0


class EnsembleDetector:
    """Weighted fusion of multiple detectors with percentile-based threshold."""

    def __init__(
        self,
        detectors: list[Detector],
        names: list[str],
        weights: list[float] | None = None,
        calibration_percentile: float = 95.0,
    ) -> None:
        if not detectors:
            msg = "At least one detector is required"
            raise ValueError(msg)
        if len(names) != len(detectors):
            msg = "names length must match detectors length"
            raise ValueError(msg)

        normalized_weights = _normalize_weights(weights or [1.0] * len(detectors))
        self._states = [
            _DetectorState(detector=detector, name=name, weight=weight)
            for detector, name, weight in zip(detectors, names, normalized_weights, strict=True)
        ]
        self._calibration_percentile = calibration_percentile
        self._threshold: float | None = None

    @property
    def threshold(self) -> float | None:
        return self._threshold

    @property
    def states(self) -> list[_DetectorState]:
        return list(self._states)

    @property
    def detector_names(self) -> list[str]:
        return [state.name for state in self._states]

    def fit(self, data: list[dict[str, Any]]) -> None:
        for state in self._states:
            state.detector.fit(data)
            fit_scores = state.detector.score(data)
            state.score_min, state.score_max = _score_bounds(fit_scores)

        combined = self.score(data)
        self._threshold = percentile_threshold(combined, self._calibration_percentile)
        logger.debug(
            "ensemble_fitted",
            threshold=self._threshold,
            percentile=self._calibration_percentile,
        )

    def score(self, data: list[dict[str, Any]]) -> list[float]:
        if not data:
            return []

        combined = [0.0] * len(data)
        for state in self._states:
            raw_scores = state.detector.score(data)
            normalized = _min_max_normalize(raw_scores, state.score_min, state.score_max)
            combined = [
                total + state.weight * score for total, score in zip(combined, normalized, strict=True)
            ]
        return combined

    def predict(self, data: list[dict[str, Any]]) -> list[bool]:
        if self._threshold is None:
            msg = "EnsembleDetector must be fitted before predicting"
            raise RuntimeError(msg)
        scores = self.score(data)
        return [score > self._threshold for score in scores]

    def individual_scores(self, data: list[dict[str, Any]]) -> dict[str, list[float]]:
        result: dict[str, list[float]] = {}
        for state in self._states:
            result[state.name] = state.detector.score(data)
        return result


def _normalize_weights(weights: list[float]) -> list[float]:
    total = sum(weights)
    if total <= 0:
        msg = "weights must sum to a positive value"
        raise ValueError(msg)
    return [weight / total for weight in weights]


def _score_bounds(scores: list[float]) -> tuple[float, float]:
    if not scores:
        return 0.0, 1.0
    return min(scores), max(scores)


def _min_max_normalize(scores: list[float], min_val: float, max_val: float) -> list[float]:
    if max_val == min_val:
        return [0.0] * len(scores)
    return [(score - min_val) / (max_val - min_val) for score in scores]
