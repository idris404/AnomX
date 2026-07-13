"""Build composite explanations for ensemble alerts."""

from __future__ import annotations

from typing import Any

from anomx.core.ensemble import EnsembleDetector
from anomx.detectors.isolation_forest import IsolationForestDetector
from anomx.detectors.mad import MADDetector
from anomx.explain.mad_rules import explain_mad
from anomx.explain.models import DetectorExplanation, Explanation
from anomx.explain.if_attribution import explain_isolation_forest


class ExplanationBuilder:
    """Produces human-readable explanations for ensemble alerts."""

    def __init__(
        self,
        ensemble: EnsembleDetector,
        fit_data: list[dict[str, Any]],
        *,
        value_key: str = "value",
        ensemble_threshold: float,
    ) -> None:
        self._ensemble = ensemble
        self._fit_data = fit_data
        self._value_key = value_key
        self._ensemble_threshold = ensemble_threshold

    def build(
        self,
        record: dict[str, Any],
        *,
        detector_scores: dict[str, float],
        ensemble_score: float,
    ) -> Explanation:
        detector_explanations = []
        feature_contributions: dict[str, float] = {}

        for state in self._ensemble.states:
            score = detector_scores[state.name]
            if isinstance(state.detector, MADDetector):
                explanation = explain_mad(state.detector, record, score)
            elif isinstance(state.detector, IsolationForestDetector):
                explanation = explain_isolation_forest(
                    state.detector,
                    record,
                    self._fit_data,
                    score,
                )
            else:
                explanation = _generic_explanation(state.name, score)
            detector_explanations.append(explanation)
            for key, value in explanation.contributions.items():
                feature_contributions[key] = feature_contributions.get(key, 0.0) + value * state.weight

        primary = max(detector_scores, key=detector_scores.get)
        primary_summary = next(
            item.summary for item in detector_explanations if item.detector == primary
        )
        observed_at = record["observed_at"]
        observed_str = observed_at.isoformat() if hasattr(observed_at, "isoformat") else str(observed_at)

        summary = (
            f"Ensemble alert (score={ensemble_score:.3f}, threshold={self._ensemble_threshold:.3f}). "
            f"Primary signal: {primary_summary}"
        )
        rules = [
            f"Ensemble score {ensemble_score:.3f} exceeded threshold {self._ensemble_threshold:.3f}",
            *[rule for item in detector_explanations for rule in item.rules],
        ]

        return Explanation(
            summary=summary,
            primary_detector=primary,
            ensemble_score=round(ensemble_score, 4),
            ensemble_threshold=round(self._ensemble_threshold, 4),
            observed_at=observed_str,
            value=float(record[self._value_key]) if self._value_key in record else None,
            detector_scores={key: round(value, 4) for key, value in detector_scores.items()},
            feature_contributions={key: round(value, 4) for key, value in feature_contributions.items()},
            rules=rules,
            detectors=detector_explanations,
        )


def _generic_explanation(name: str, score: float) -> DetectorExplanation:
    return DetectorExplanation(
        detector=name,
        summary=f"{name} score={score:.3f}",
        rules=[f"{name} contributed score {score:.3f}"],
        contributions={},
        details={},
    )
