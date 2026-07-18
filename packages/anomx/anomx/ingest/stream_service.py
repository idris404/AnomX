"""Streaming ingestion orchestration."""

from __future__ import annotations

import hashlib
import json
from typing import Any
from uuid import UUID

import structlog
from pydantic import BaseModel, Field

from anomx.config.models import DatabaseSettings, KafkaJsonSourceConfig
from anomx.connectors.kafka_json import KafkaJsonSource
from anomx.detect.service import DetectService
from anomx.ingest.service import row_fingerprint
from anomx.storage.ingestion import IngestionRepository
from anomx.storage.postgres import postgres_connection

logger = structlog.get_logger(__name__)


class StreamIngestResult(BaseModel):
    """Outcome of a Kafka micro-batch ingestion run."""

    run_id: UUID | None = None
    stream_id: UUID | None = None
    stream_name: str
    records_read: int
    records_written: int
    kafka_offsets: list[dict[str, int | str]] = Field(default_factory=list)
    detect_run_id: UUID | None = None
    alerts_created: int | None = None
    mlflow_run_id: str | None = None
    empty_batch: bool = False


class StreamIngestService:
    """Consumes Kafka JSON micro-batches and persists observations."""

    def __init__(self, database: DatabaseSettings) -> None:
        self._database = database

    async def consume_batch(
        self,
        config: KafkaJsonSourceConfig,
        *,
        max_messages: int = 500,
        timeout_ms: int = 5_000,
        detect_after: bool = False,
        detect_config_path: str = "config/detectors.yaml",
        settings_path: str = "config/settings.yaml",
    ) -> StreamIngestResult:
        source = KafkaJsonSource(
            bootstrap_servers=config.bootstrap_servers,
            topic=config.topic,
            group_id=config.group_id,
            timestamp_field=config.timestamp_field,
            value_field=config.value_field,
            auto_offset_reset=config.auto_offset_reset,
        )

        try:
            records, offsets = await source.poll_batch(
                max_messages=max_messages,
                timeout_ms=timeout_ms,
            )
            if not records:
                logger.info("stream_ingest_empty_batch", stream=config.name, topic=config.topic)
                return StreamIngestResult(
                    stream_name=config.name,
                    records_read=0,
                    records_written=0,
                    empty_batch=True,
                )

            content_hash = _batch_content_hash(records, offsets)
            with postgres_connection(self._database.dsn) as connection:
                repository = IngestionRepository(connection)
                stream_id = repository.get_or_create_stream(
                    name=config.name,
                    source_type=config.source_type,
                    config=config.model_dump(mode="json"),
                )
                run_id = repository.create_run(
                    stream_id=stream_id,
                    metadata={
                        "source_type": config.source_type,
                        "topic": config.topic,
                        "content_hash": content_hash,
                        "kafka_offsets": offsets,
                    },
                )

                try:
                    prepared = [
                        {
                            "observed_at": record["observed_at"],
                            "payload": record["payload"],
                            "row_fingerprint": row_fingerprint(
                                stream_id,
                                record["observed_at"],
                                record["payload"],
                            ),
                        }
                        for record in records
                    ]
                    written = repository.insert_observations(run_id, stream_id, prepared)
                    repository.complete_run(
                        run_id,
                        {
                            "topic": config.topic,
                            "content_hash": content_hash,
                            "kafka_offsets": offsets,
                        },
                        row_count=written,
                    )
                except Exception as exc:
                    repository.fail_run(run_id, str(exc))
                    logger.exception("stream_ingest_failed", stream=config.name, run_id=str(run_id))
                    raise

            await source.commit()
        finally:
            await source.close()

        logger.info(
            "stream_ingest_complete",
            stream=config.name,
            run_id=str(run_id),
            records_read=len(records),
            records_written=written,
        )

        detect_run_id: UUID | None = None
        alerts_created: int | None = None
        mlflow_run_id: str | None = None
        if detect_after and written > 0:
            from pathlib import Path

            from anomx.config.loader import load_app_settings, load_detect_config
            from anomx.mlops.tracker import log_detect_run_if_enabled

            detect_path = Path(detect_config_path)
            settings = load_app_settings(Path(settings_path))
            detect_config = load_detect_config(detect_path)
            detect_result = DetectService(database=self._database).detect_stream(
                config.name,
                detect_config,
            )
            detect_run_id = detect_result.run_id
            alerts_created = detect_result.alerts_created
            mlflow_run_id = log_detect_run_if_enabled(
                settings.mlflow,
                detect_result,
                detect_config,
                detect_config_path=detect_path,
            )

        return StreamIngestResult(
            run_id=run_id,
            stream_id=stream_id,
            stream_name=config.name,
            records_read=len(records),
            records_written=written,
            kafka_offsets=offsets,
            detect_run_id=detect_run_id,
            alerts_created=alerts_created,
            mlflow_run_id=mlflow_run_id,
        )


def _batch_content_hash(
    records: list[dict[str, Any]],
    offsets: list[dict[str, int | str]],
) -> str:
    canonical = json.dumps(
        {
            "records": [
                {
                    "observed_at": record["observed_at"].isoformat(),
                    "payload": record["payload"],
                }
                for record in records
            ],
            "offsets": offsets,
        },
        sort_keys=True,
        default=str,
    )
    return hashlib.sha256(canonical.encode()).hexdigest()
