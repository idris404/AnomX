"""Build detector instances from configuration."""

from __future__ import annotations

from typing import Any

from anomx.core.interfaces import Detector
from anomx.detectors.isolation_forest import IsolationForestDetector
from anomx.detectors.mad import MADDetector


def build_detector(detector_type: str, params: dict[str, Any] | None = None) -> Detector:
    params = params or {}
    if detector_type == "mad":
        return MADDetector(value_key=params.get("value_key", "value"))
    if detector_type == "isolation_forest":
        return IsolationForestDetector(
            feature_keys=params.get("feature_keys", ["value"]),
            contamination=float(params.get("contamination", 0.05)),
            random_state=int(params.get("random_state", 42)),
        )
    msg = f"Unknown detector type: {detector_type}"
    raise ValueError(msg)
