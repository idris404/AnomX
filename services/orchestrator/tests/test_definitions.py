"""Smoke tests for Dagster definitions."""

from anomx_orchestrator.definitions import defs


def test_definitions_loads() -> None:
    assert defs is not None


def test_definitions_exposes_pipeline_assets() -> None:
    asset_keys = {key.path[-1] for key in defs.resolve_all_asset_keys()}
    assert "ingestion_run" in asset_keys
    assert "detection_run" in asset_keys


def test_definitions_exposes_sample_csv_job() -> None:
    job = defs.resolve_job_def("sample_csv_pipeline")
    assert job.name == "sample_csv_pipeline"
