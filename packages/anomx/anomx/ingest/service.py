"""Batch ingestion orchestration."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID

import structlog
from pydantic import BaseModel, Field

from anomx.config.models import CsvBatchSourceConfig, DatabaseSettings, SourceConfig
from anomx.connectors.factory import build_source
from anomx.storage.ingestion import IngestionRepository
from anomx.storage.postgres import postgres_connection

logger = structlog.get_logger(__name__)

_FILE_SOURCE_TYPES = {"csv_batch", "nab_batch", "online_retail_batch"}


class IngestResult(BaseModel):
    """Outcome of a batch ingestion run."""

    run_id: UUID
    stream_id: UUID
    stream_name: str
    records_read: int
    records_written: int
    content_hash: str
    skipped: bool = Field(
        description="True when an identical file was already ingested for this stream",
    )


class IngestService:
    """Coordinates source read, validation, and Postgres persistence."""

    def __init__(self, database: DatabaseSettings) -> None:
        self._database = database

    def ingest(self, config: SourceConfig) -> IngestResult:
        source = build_source(config, database=self._database)

        with postgres_connection(self._database.dsn) as connection:
            repository = IngestionRepository(connection)
            stream_id = repository.get_or_create_stream(
                name=config.name,
                source_type=config.source_type,
                config=config.model_dump(mode="json"),
            )

            if config.source_type in _FILE_SOURCE_TYPES:
                content_hash = _file_content_hash(config)
                existing_run = repository.find_completed_run_by_content_hash(stream_id, content_hash)
                if existing_run is not None:
                    return _skipped_result(existing_run, stream_id, config.name, content_hash)
                records = source.read()
            else:
                records = source.read()
                content_hash = records_content_hash(records)
                existing_run = repository.find_completed_run_by_content_hash(stream_id, content_hash)
                if existing_run is not None:
                    return _skipped_result(existing_run, stream_id, config.name, content_hash)

            run_id = repository.create_run(
                stream_id=stream_id,
                metadata={
                    "content_hash": content_hash,
                    "source_type": config.source_type,
                    **_source_run_metadata(config),
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
                        "content_hash": content_hash,
                        **_source_run_metadata(config),
                    },
                    row_count=written,
                )
            except Exception as exc:
                repository.fail_run(run_id, str(exc))
                logger.exception("ingest_failed", stream=config.name, run_id=str(run_id))
                raise

            logger.info(
                "ingest_complete",
                stream=config.name,
                run_id=str(run_id),
                records_read=len(records),
                records_written=written,
            )
            return IngestResult(
                run_id=run_id,
                stream_id=stream_id,
                stream_name=config.name,
                records_read=len(records),
                records_written=written,
                content_hash=content_hash,
                skipped=False,
            )

    def ingest_csv_batch(self, config: CsvBatchSourceConfig) -> IngestResult:
        return self.ingest(config)


def _skipped_result(
    existing_run: dict[str, Any],
    stream_id: UUID,
    stream_name: str,
    content_hash: str,
) -> IngestResult:
    run_id = UUID(str(existing_run["id"]))
    metadata = existing_run["metadata"]
    row_count = int(metadata.get("row_count", 0)) if isinstance(metadata, dict) else 0
    logger.info(
        "ingest_skipped_idempotent",
        stream=stream_name,
        run_id=str(run_id),
        content_hash=content_hash,
    )
    return IngestResult(
        run_id=run_id,
        stream_id=stream_id,
        stream_name=stream_name,
        records_read=row_count,
        records_written=0,
        content_hash=content_hash,
        skipped=True,
    )


def _source_run_metadata(config: SourceConfig) -> dict[str, Any]:
    if config.source_type in _FILE_SOURCE_TYPES:
        return {"source_path": str(config.path)}
    if config.source_type == "postgres_query":
        return {"query": config.query}
    return {}


def _file_content_hash(config: SourceConfig) -> str:
    path = getattr(config, "path", None)
    if path is None:
        msg = "File source config missing path"
        raise ValueError(msg)
    return file_content_hash(path)


def file_content_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def records_content_hash(records: list[dict[str, Any]]) -> str:
    canonical = json.dumps(
        [
            {
                "observed_at": record["observed_at"].isoformat(),
                "payload": record["payload"],
            }
            for record in records
        ],
        sort_keys=True,
        default=str,
    )
    return hashlib.sha256(canonical.encode()).hexdigest()


def row_fingerprint(stream_id: UUID, observed_at: datetime, payload: dict[str, Any]) -> str:
    content = f"{stream_id}|{observed_at.isoformat()}|{json.dumps(payload, sort_keys=True, default=str)}"
    return hashlib.sha256(content.encode()).hexdigest()
