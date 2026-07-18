"""Pipeline run history queries."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from anomx.config.models import DatabaseSettings
from anomx.storage.postgres import postgres_connection
from anomx.storage.runs import RunsRepository


class RunSummary(BaseModel):
    run_id: str
    run_type: str
    status: str
    started_at: str
    finished_at: str | None = None
    observations_scored: int | None = None
    alerts_created: int | None = None
    records_written: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class RunService:
    """Read-side run history for API, CLI, and observability."""

    def __init__(self, database: DatabaseSettings) -> None:
        self._database = database

    def list_runs_for_stream(self, stream_name: str, *, limit: int = 20) -> list[RunSummary]:
        with postgres_connection(self._database.dsn) as connection:
            repository = RunsRepository(connection)
            stream = repository.get_stream_by_name(stream_name)
            if stream is None:
                msg = f"Stream not found: {stream_name}"
                raise ValueError(msg)

            stream_id = UUID(str(stream["id"]))
            rows = repository.list_runs_for_stream(stream_id, limit=limit)
            return [_to_summary(row) for row in rows]


def _to_summary(row: dict[str, Any]) -> RunSummary:
    metadata = row.get("metadata")
    if not isinstance(metadata, dict):
        metadata = {}

    run_type = str(metadata.get("run_type", "ingestion"))

    return RunSummary(
        run_id=str(row["id"]),
        run_type=run_type,
        status=str(row["status"]),
        started_at=_format_timestamp(row.get("started_at")),
        finished_at=_format_timestamp(row.get("finished_at")),
        observations_scored=_optional_int(metadata.get("observations_scored")),
        alerts_created=_optional_int(metadata.get("alerts_created")),
        records_written=_optional_int(metadata.get("row_count")),
        metadata=metadata,
    )


def _format_timestamp(value: Any) -> str | None:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)
