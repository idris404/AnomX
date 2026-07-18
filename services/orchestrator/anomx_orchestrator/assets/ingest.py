"""Dagster assets for batch ingestion."""

from typing import Any

from dagster import Config, asset

from anomx.config.loader import load_app_settings, load_source_config
from anomx.ingest.service import IngestService
from anomx_orchestrator.paths import repo_path, repo_root


class IngestAssetConfig(Config):
    source_config_path: str = "config/sources/sample_csv.yaml"
    settings_path: str = "config/settings.yaml"


@asset(
    description="Batch ingestion run — persists observations to Postgres.",
    group_name="stream_pipeline",
)
def ingestion_run(config: IngestAssetConfig) -> dict[str, Any]:
    app_settings = load_app_settings(repo_path(config.settings_path))
    source_config = load_source_config(
        repo_path(config.source_config_path),
        path_base=repo_root(),
    )
    result = IngestService(database=app_settings.database).ingest(source_config)
    return result.model_dump(mode="json")
