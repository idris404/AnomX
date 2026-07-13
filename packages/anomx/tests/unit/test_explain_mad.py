"""Tests for MAD rule-based explanations."""

from anomx.detectors.mad import MADDetector
from anomx.explain.mad_rules import explain_mad


def test_mad_explanation_is_human_readable() -> None:
    records = [{"value": float(20 + index * 0.1)} for index in range(100)]
    records.append({"value": 99.0})

    detector = MADDetector()
    detector.fit(records[:-1])
    score = detector.score([records[-1]])[0]

    explanation = explain_mad(detector, records[-1], score)

    assert "median" in explanation.summary.lower()
    assert len(explanation.rules) >= 3
    assert "threshold" in explanation.rules[-1].lower()
    assert explanation.contributions["value"] > 0
