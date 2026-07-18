"""PostgreSQL persistence for pipeline run history."""

from __future__ import annotations

from typing import Any
from uuid import UUID

import psycopg


class RunsRepository:
    """Lists ingestion and detection runs for operational visibility."""

    def __init__(self, connection: psycopg.Connection[Any]) -> None:
        self._connection = connection

    def get_stream_by_name(self, name: str) -> dict[str, Any] | None:
        return self._connection.execute(
            "SELECT id, name FROM streams WHERE name = %s",
            (name,),
        ).fetchone()

    def list_runs_for_stream(self, stream_id: UUID, *, limit: int = 20) -> list[dict[str, Any]]:
        rows = self._connection.execute(
            """
            SELECT id, status, started_at, finished_at, metadata
            FROM runs
            WHERE stream_id = %s
            ORDER BY started_at DESC
            LIMIT %s
            """,
            (stream_id, limit),
        ).fetchall()
        return [dict(row) for row in rows]
