"""MLflow experiment tracking for detection runs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import structlog

from anomx.config.detect_models import DetectConfig
from anomx.config.models import MlflowSettings
from anomx.detect.service import DetectResult

logger = structlog.get_logger(__name__)


class MlflowDetectTracker:
    """Logs detection params and metrics to MLflow when enabled."""

    def __init__(self, settings: MlflowSettings) -> None:
        self._settings = settings

    @property
    def enabled(self) -> bool:
        return self._settings.enabled

    def log_detect_run(
        self,
        result: DetectResult,
        config: DetectConfig,
        *,
        detect_config_path: Path | None = None,
    ) -> str | None:
        if not self._settings.enabled:
            return None

        import mlflow

        tracking_uri = self._settings.tracking_uri
        if tracking_uri.startswith("sqlite:///"):
            db_path = tracking_uri.removeprefix("sqlite:///")
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        mlflow.set_tracking_uri(tracking_uri)
        mlflow.set_experiment(self._settings.experiment_name)

        run_name = f"detect-{result.stream_name}-{str(result.run_id)[:8]}"
        with mlflow.start_run(run_name=run_name) as active_run:
            mlflow.set_tags(
                {
                    "stream_name": result.stream_name,
                    "postgres_run_id": str(result.run_id),
                    "source_run_id": str(result.source_run_id),
                }
            )
            mlflow.log_params(detect_config_params(config))
            mlflow.log_metrics(
                {
                    "observations_scored": float(result.observations_scored),
                    "alerts_created": float(result.alerts_created),
                    "ensemble_threshold": float(result.ensemble_threshold),
                }
            )
            if detect_config_path is not None and detect_config_path.is_file():
                mlflow.log_artifact(str(detect_config_path), artifact_path="config")

            mlflow_run_id = active_run.info.run_id
            logger.info(
                "mlflow_detect_logged",
                stream=result.stream_name,
                mlflow_run_id=mlflow_run_id,
            )
            return mlflow_run_id


def detect_config_params(config: DetectConfig) -> dict[str, str]:
    """Flatten detector config into MLflow-safe string params."""
    params: dict[str, str] = {
        "calibration_percentile": str(config.defaults.calibration.percentile),
        "fit_ratio": str(config.defaults.fit_ratio),
        "value_key": config.defaults.value_key,
        "detectors_json": json.dumps(
            [
                {
                    "name": item.name,
                    "type": item.type,
                    "weight": item.weight,
                    "params": item.params,
                }
                for item in config.detectors
            ],
            sort_keys=True,
        ),
    }
    for item in config.detectors:
        params[f"detector.{item.name}.type"] = item.type
        params[f"detector.{item.name}.weight"] = str(item.weight)
    return params


def log_detect_run_if_enabled(
    settings: MlflowSettings,
    result: DetectResult,
    config: DetectConfig,
    *,
    detect_config_path: Path | None = None,
) -> str | None:
    return MlflowDetectTracker(settings).log_detect_run(
        result,
        config,
        detect_config_path=detect_config_path,
    )
