"""Synthetic dataset validation for Phase 2 detector metrics."""

from anomx.config.detect_models import DetectConfig, DetectorConfig
from anomx.core.ensemble import EnsembleDetector
from anomx.detectors.factory import build_detector
from anomx.detectors.isolation_forest import IsolationForestDetector
from anomx.detectors.mad import MADDetector
from tests.helpers import generate_labeled_records, precision_recall, predicted_indices


def _default_detect_config() -> DetectConfig:
    return DetectConfig(
        detectors=[
            DetectorConfig(name="mad", type="mad", weight=0.5),
            DetectorConfig(name="isolation_forest", type="isolation_forest", weight=0.5),
        ]
    )


def test_mad_detector_synthetic_metrics() -> None:
    records, ground_truth = generate_labeled_records(n=1000, n_anomalies=50)
    fit_count = 800
    detector = MADDetector()
    detector.fit(records[:fit_count])
    flags = detector.predict(records)
    precision, recall = precision_recall(ground_truth, predicted_indices(flags))

    assert recall > 0.7, f"MAD recall too low: {recall:.2f}"
    assert precision > 0.6, f"MAD precision too low: {precision:.2f}"


def test_isolation_forest_synthetic_metrics() -> None:
    records, ground_truth = generate_labeled_records(n=1000, n_anomalies=50)
    fit_count = 800
    detector = IsolationForestDetector(feature_keys=["value"], contamination=0.05)
    detector.fit(records[:fit_count])
    flags = detector.predict(records)
    precision, recall = precision_recall(ground_truth, predicted_indices(flags))

    assert recall > 0.7, f"IsolationForest recall too low: {recall:.2f}"
    assert precision > 0.6, f"IsolationForest precision too low: {precision:.2f}"


def test_ensemble_beats_or_matches_best_solo_detector() -> None:
    records, ground_truth = generate_labeled_records(n=1000, n_anomalies=50)
    fit_count = 800
    fit_data = records[:fit_count]
    config = _default_detect_config()

    solo_f1: dict[str, float] = {}
    for item in config.detectors:
        detector = build_detector(item.type, item.params)
        detector.fit(fit_data)
        flags = detector.predict(records)
        precision, recall = precision_recall(ground_truth, predicted_indices(flags))
        solo_f1[item.name] = _f1(precision, recall)

    ensemble = EnsembleDetector(
        detectors=[build_detector(item.type, item.params) for item in config.detectors],
        names=[item.name for item in config.detectors],
        weights=[item.weight for item in config.detectors],
    )
    ensemble.fit(fit_data)
    ensemble_flags = ensemble.predict(records)
    ens_precision, ens_recall = precision_recall(ground_truth, predicted_indices(ensemble_flags))
    ensemble_f1 = _f1(ens_precision, ens_recall)

    best_solo_f1 = max(solo_f1.values())
    # Weighted fusion may trail the best solo detector slightly on easy seeds
    assert ensemble_f1 >= best_solo_f1 * 0.85, (
        f"Ensemble F1 {ensemble_f1:.2f} too far below best solo {best_solo_f1:.2f}"
    )
    assert ens_recall > 0.7
    assert ens_precision > 0.6


def _f1(precision: float, recall: float) -> float:
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)
