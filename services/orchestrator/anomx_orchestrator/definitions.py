"""Dagster code location for AnomX."""

from dagster import Definitions, RunConfig, define_asset_job

from anomx_orchestrator.assets import detection_run, ingestion_run
from anomx_orchestrator.assets.ingest import IngestAssetConfig

stream_pipeline_job = define_asset_job(
    name="stream_pipeline",
    selection=[ingestion_run, detection_run],
    description="Ingest a configured source then run ensemble detection.",
)

sample_csv_pipeline_job = define_asset_job(
    name="sample_csv_pipeline",
    selection=[ingestion_run, detection_run],
    config=RunConfig(
        ops={
            "ingestion_run": IngestAssetConfig(source_config_path="config/sources/sample_csv.yaml"),
        }
    ),
)

nab_pipeline_job = define_asset_job(
    name="nab_pipeline",
    selection=[ingestion_run, detection_run],
    config=RunConfig(
        ops={
            "ingestion_run": IngestAssetConfig(
                source_config_path="config/sources/nab_cpu_utilization.yaml",
            ),
        }
    ),
)

defs = Definitions(
    assets=[ingestion_run, detection_run],
    jobs=[stream_pipeline_job, sample_csv_pipeline_job, nab_pipeline_job],
)
