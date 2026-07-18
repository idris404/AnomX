"""Unit tests for pipeline assets with mocked services."""

from __future__ import annotations

from unittest.mock import MagicMock, patch
from uuid import uuid4

from anomx_orchestrator.assets.detect import detection_run
from anomx_orchestrator.assets.ingest import IngestAssetConfig, ingestion_run


@patch("anomx_orchestrator.assets.ingest.IngestService")
@patch("anomx_orchestrator.assets.ingest.load_source_config")
@patch("anomx_orchestrator.assets.ingest.load_app_settings")
def test_ingestion_run_asset_returns_payload(
    mock_settings: MagicMock,
    mock_source_config: MagicMock,
    mock_service_cls: MagicMock,
) -> None:
    run_id = uuid4()
    stream_id = uuid4()
    mock_result = MagicMock()
    mock_result.model_dump.return_value = {
        "run_id": str(run_id),
        "stream_id": str(stream_id),
        "stream_name": "sample_csv",
        "records_read": 200,
        "records_written": 200,
        "content_hash": "abc",
        "skipped": False,
    }
    mock_result.stream_name = "sample_csv"
    mock_result.records_read = 200
    mock_result.records_written = 200
    mock_result.skipped = False
    mock_result.content_hash = "abc"
    mock_result.run_id = run_id
    mock_service_cls.return_value.ingest.return_value = mock_result

    payload = ingestion_run(IngestAssetConfig())

    assert payload["stream_name"] == "sample_csv"
    assert payload["records_written"] == 200


@patch("anomx_orchestrator.assets.detect.DetectService")
@patch("anomx_orchestrator.assets.detect.load_detect_config")
@patch("anomx_orchestrator.assets.detect.load_app_settings")
def test_detection_run_asset_uses_ingestion_stream(
    mock_settings: MagicMock,
    mock_detect_config: MagicMock,
    mock_service_cls: MagicMock,
) -> None:
    run_id = uuid4()
    stream_id = uuid4()
    source_run_id = uuid4()
    mock_result = MagicMock()
    mock_result.model_dump.return_value = {
        "run_id": str(run_id),
        "stream_id": str(stream_id),
        "stream_name": "sample_csv",
        "source_run_id": str(source_run_id),
        "observations_scored": 200,
        "alerts_created": 12,
        "ensemble_threshold": 0.27,
    }
    mock_result.stream_name = "sample_csv"
    mock_result.observations_scored = 200
    mock_result.alerts_created = 12
    mock_result.ensemble_threshold = 0.27
    mock_result.run_id = run_id
    mock_service_cls.return_value.detect_stream.return_value = mock_result

    payload = detection_run(ingestion_run={"stream_name": "sample_csv"})

    mock_service_cls.return_value.detect_stream.assert_called_once()
    assert payload["alerts_created"] == 12
