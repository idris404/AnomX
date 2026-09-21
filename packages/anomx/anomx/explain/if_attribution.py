"""Feature attribution for Isolation Forest by median replacement."""

from __future__ import annotations

from typing import Any

import numpy as np

from anomx.detectors.isolation_forest import IsolationForestDetector, _feature_matrix
from anomx.explain.models import DetectorExplanation


def explain_isolation_forest(
    detector: IsolationForestDetector,
    record: dict[str, Any],
    fit_data: list[dict[str, Any]],
    score: float,
    *,
    max_background: int = 50,
) -> DetectorExplanation:
    """Attribute IF predictions via feature replacement against a fit-window baseline.

    IsolationForest is not fully supported by SHAP TreeExplainer across platforms.
    This heuristic replaces each feature with its fit-window median; it is not SHAP.
    """
    if not detector.is_fitted:
        msg = "IsolationForestDetector must be fitted before explaining"
        raise RuntimeError(msg)

    keys = detector.feature_keys
    row = _feature_matrix([record], keys)
    background = _feature_matrix(fit_data[:max_background], keys)
    baseline_score = float(-detector._model.decision_function(row)[0])  # noqa: SLF001

    contributions: dict[str, float] = {}
    for feature_index, key in enumerate(keys):
        perturbed = row.copy()
        perturbed[0, feature_index] = float(np.median(background[:, feature_index]))
        perturbed_score = float(-detector._model.decision_function(perturbed)[0])  # noqa: SLF001
        contributions[key] = round(baseline_score - perturbed_score, 4)

    top_feature = max(contributions, key=lambda name: contributions[name])
    top_value = contributions[top_feature]
    summary = (
        f"Isolation Forest raw score={score:.3f}; largest median-replacement change: "
        f"{top_feature} ({top_value:+.3f})."
    )
    rules = [
        f"Model anomaly score (raw): {score:.3f}",
        "Attribution method: feature replacement with fit-window medians",
        *[f"Feature contribution {name}={value:+.4f}" for name, value in contributions.items()],
    ]

    return DetectorExplanation(
        detector="isolation_forest",
        summary=summary,
        rules=rules,
        contributions=contributions,
        details={
            "raw_score": round(score, 4),
            "attribution_method": "median_replacement",
        },
    )
