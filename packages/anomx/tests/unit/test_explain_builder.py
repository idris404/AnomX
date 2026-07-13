"""Tests for composite explanation builder."""

from datetime import UTC, datetime

from anomx.config.detect_models import DetectorConfig
from anomx.core.ensemble import EnsembleDetector
from anomx.detectors.factory import build_detector
from anomx.explain.builder import ExplanationBuilder


def _records(count: int) -> list[dict[str, float | datetime]]:
    start = datetime(2024, 1, 1, tzinfo=UTC)
    rows: list[dict[str, float | datetime]] = []
    for index in range(count):
        rows.append(
            {
                "value": 20.0 + index * 0.01,
                "observed_at": start,
            }
        )
    rows[-1]["value"] = 80.0
    return rows


def test_explanation_builder_produces_summary_and_rules() -> None:
    records = _records(120)
    fit_data = records[:100]
    target = records[-1]

    configs = [
        DetectorConfig(name="mad", type="mad", weight=0.5),
        DetectorConfig(name="isolation_forest", type="isolation_forest", weight=0.5),
    ]
    ensemble = EnsembleDetector(
        detectors=[build_detector(item.type, item.params) for item in configs],
        names=[item.name for item in configs],
        weights=[item.weight for item in configs],
    )
    ensemble.fit(fit_data)

    builder = ExplanationBuilder(
        ensemble=ensemble,
        fit_data=fit_data,
        value_key="value",
        ensemble_threshold=ensemble.threshold or 0.0,
    )
    explanation = builder.build(
        target,
        detector_scores={
            "mad": ensemble.individual_scores([target])["mad"][0],
            "isolation_forest": ensemble.individual_scores([target])["isolation_forest"][0],
        },
        ensemble_score=ensemble.score([target])[0],
    )

    assert explanation.summary.startswith("Ensemble alert")
    assert explanation.primary_detector in {"mad", "isolation_forest"}
    assert len(explanation.rules) >= 3
    assert len(explanation.detectors) == 2
    assert explanation.value is not None
