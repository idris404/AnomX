"""Rule-based explanations for MAD detector."""

from __future__ import annotations

from typing import Any

from anomx.detectors.mad import MADDetector
from anomx.explain.models import DetectorExplanation

_MAD_SCALE = 1.4826


def explain_mad(detector: MADDetector, record: dict[str, Any], score: float) -> DetectorExplanation:
    value = float(record[detector.value_key])
    robust_z = score
    direction = "above" if value >= detector.median else "below"

    summary = (
        f"Value {value:.2f} is {direction} the reference median {detector.median:.2f} "
        f"with robust z-score {robust_z:.2f} (threshold {detector.threshold:.2f})."
    )
    rules = [
        f"Reference median on fit window: {detector.median:.2f}",
        f"Median absolute deviation (MAD): {detector.mad:.4f}",
        f"Observed {detector.value_key}={value:.2f} → |x−median|/({_MAD_SCALE}×MAD)={robust_z:.2f}",
        f"Alert because robust z-score {robust_z:.2f} > threshold {detector.threshold:.2f}",
    ]

    return DetectorExplanation(
        detector="mad",
        summary=summary,
        rules=rules,
        contributions={detector.value_key: round(robust_z, 4)},
        details={
            "observed_value": value,
            "median": detector.median,
            "mad": detector.mad,
            "robust_z": round(robust_z, 4),
            "threshold": detector.threshold,
        },
    )
