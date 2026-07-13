"""Multivariate anomaly detection via Isolation Forest (sklearn)."""

from __future__ import annotations

from typing import Any

import numpy as np
import structlog
from sklearn.ensemble import IsolationForest

logger = structlog.get_logger(__name__)


class IsolationForestDetector:
    """Standard multivariate detector — no Gaussian assumption, sklearn baseline."""

    def __init__(
        self,
        feature_keys: list[str] | None = None,
        contamination: float = 0.05,
        random_state: int = 42,
    ) -> None:
        self._feature_keys = feature_keys or ["value"]
        self._model = IsolationForest(
            contamination=contamination,
            random_state=random_state,
            n_estimators=100,
        )
        self._is_fitted = False

    def fit(self, data: list[dict[str, Any]]) -> None:
        matrix = _feature_matrix(data, self._feature_keys)
        if matrix.shape[0] < 2:
            msg = "IsolationForestDetector.fit requires at least 2 observations"
            raise ValueError(msg)
        self._model.fit(matrix)
        self._is_fitted = True
        logger.debug("isolation_forest_fitted", n_samples=matrix.shape[0], n_features=matrix.shape[1])

    def score(self, data: list[dict[str, Any]]) -> list[float]:
        if not self._is_fitted:
            msg = "IsolationForestDetector must be fitted before scoring"
            raise RuntimeError(msg)
        matrix = _feature_matrix(data, self._feature_keys)
        # Higher score = more anomalous (invert sklearn decision function)
        raw = -self._model.decision_function(matrix)
        min_val = float(np.min(raw))
        max_val = float(np.max(raw))
        if max_val == min_val:
            return [0.0] * len(raw)
        normalized = (raw - min_val) / (max_val - min_val)
        return [float(value) for value in normalized]

    def predict(self, data: list[dict[str, Any]]) -> list[bool]:
        if not self._is_fitted:
            msg = "IsolationForestDetector must be fitted before predicting"
            raise RuntimeError(msg)
        matrix = _feature_matrix(data, self._feature_keys)
        predictions = self._model.predict(matrix)
        return [prediction == -1 for prediction in predictions]


def _feature_matrix(data: list[dict[str, Any]], feature_keys: list[str]) -> np.ndarray:
    rows: list[list[float]] = []
    for record in data:
        rows.append([float(record[key]) for key in feature_keys])
    return np.array(rows, dtype=np.float64)
