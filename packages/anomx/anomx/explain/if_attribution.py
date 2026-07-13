"""Feature attribution for Isolation Forest (permutation-based, SHAP-compatible output)."""

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
    """Attribute IF predictions via input perturbation against a fit-window baseline.

    IsolationForest is not fully supported by SHAP TreeExplainer across platforms.
    Permutation attribution is used for MVP portability (Windows/Python 3.11).
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

    top_feature = max(contributions, key=contributions.get)
    top_value = contributions[top_feature]
    summary = (
        f"Isolation Forest flagged the point (score={score:.3f}); "
        f"strongest driver: {top_feature} (contribution {top_value:+.3f})."
    )
    rules = [
        f"Model anomaly score (normalized): {score:.3f}",
        "Attribution method: permutation vs fit-window medians",
        *[f"Feature contribution {name}={value:+.4f}" for name, value in contributions.items()],
    ]

    return DetectorExplanation(
        detector="isolation_forest",
        summary=summary,
        rules=rules,
        contributions=contributions,
        details={
            "normalized_score": round(score, 4),
            "attribution_method": "permutation",
        },
    )
