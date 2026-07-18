"""Dagster assets for anomaly detection."""

from typing import Any

from dagster import asset

from anomx.config.loader import load_app_settings, load_detect_config
from anomx.detect.service import DetectService
from anomx_orchestrator.paths import repo_path

DEFAULT_DETECT_CONFIG = "config/detectors.yaml"
DEFAULT_SETTINGS = "config/settings.yaml"


@asset(
    deps=["ingestion_run"],
    description="Detection run — scores observations and persists alerts with explanations.",
    group_name="stream_pipeline",
)
def detection_run(ingestion_run: dict[str, Any]) -> dict[str, Any]:
    stream_name = str(ingestion_run["stream_name"])
    app_settings = load_app_settings(repo_path(DEFAULT_SETTINGS))
    detect_config = load_detect_config(repo_path(DEFAULT_DETECT_CONFIG))
    result = DetectService(database=app_settings.database).detect_stream(stream_name, detect_config)
    return result.model_dump(mode="json")
