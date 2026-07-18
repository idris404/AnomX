"""Unit tests for MLflow detect tracking helpers."""

from pathlib import Path
from uuid import uuid4

from anomx.config.detect_models import DetectConfig, DetectDefaults, DetectorConfig
from anomx.config.models import MlflowSettings
from anomx.detect.service import DetectResult
from anomx.mlops.tracker import MlflowDetectTracker, detect_config_params


def test_detect_config_params_flattens_detectors() -> None:
    config = DetectConfig(
        defaults=DetectDefaults(),
        detectors=[
            DetectorConfig(name="mad", type="mad", weight=0.5, params={"value_key": "value"}),
            DetectorConfig(
                name="isolation_forest",
                type="isolation_forest",
                weight=0.5,
                params={"feature_keys": ["value"]},
            ),
        ],
    )

    params = detect_config_params(config)

    assert params["calibration_percentile"] == "95.0"
    assert params["detector.mad.type"] == "mad"
    assert "detectors_json" in params


def test_mlflow_tracker_disabled_returns_none() -> None:
    tracker = MlflowDetectTracker(MlflowSettings(enabled=False))
    result = DetectResult(
        run_id=uuid4(),
        stream_id=uuid4(),
        stream_name="demo",
        source_run_id=uuid4(),
        observations_scored=100,
        alerts_created=3,
        ensemble_threshold=0.27,
    )
    config = DetectConfig(
        defaults=DetectDefaults(),
        detectors=[DetectorConfig(name="mad", type="mad", weight=1.0, params={})],
    )

    assert tracker.log_detect_run(result, config, detect_config_path=Path("config/detectors.yaml")) is None
