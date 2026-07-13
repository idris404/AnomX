"""PostgreSQL persistence for batch ingestion."""

from __future__ import annotations

from typing import Any
from uuid import UUID

import psycopg
from psycopg.types.json import Jsonb


class IngestionRepository:
    """Persists streams, ingestion runs, and raw observations."""

    def __init__(self, connection: psycopg.Connection[Any]) -> None:
        self._connection = connection

    def get_or_create_stream(
        self,
        name: str,
        source_type: str,
        config: dict[str, Any],
    ) -> UUID:
        row = self._connection.execute(
            """
            INSERT INTO streams (name, source_type, config)
            VALUES (%s, %s, %s)
            ON CONFLICT (name) DO UPDATE
            SET source_type = EXCLUDED.source_type,
                config = EXCLUDED.config,
                updated_at = now()
            RETURNING id
            """,
            (name, source_type, Jsonb(config)),
        ).fetchone()
        assert row is not None
        return UUID(str(row["id"]))

    def find_completed_run_by_content_hash(
        self,
        stream_id: UUID,
        content_hash: str,
    ) -> dict[str, Any] | None:
        row = self._connection.execute(
            """
            SELECT id, metadata
            FROM runs
            WHERE stream_id = %s
              AND status = 'completed'
              AND metadata->>'content_hash' = %s
            LIMIT 1
            """,
            (stream_id, content_hash),
        ).fetchone()
        return row

    def create_run(self, stream_id: UUID, metadata: dict[str, Any]) -> UUID:
        row = self._connection.execute(
            """
            INSERT INTO runs (stream_id, status, metadata)
            VALUES (%s, 'running', %s)
            RETURNING id
            """,
            (stream_id, Jsonb(metadata)),
        ).fetchone()
        assert row is not None
        return UUID(str(row["id"]))

    def complete_run(
        self,
        run_id: UUID,
        metadata: dict[str, Any],
        *,
        row_count: int,
    ) -> None:
        merged = {**metadata, "row_count": row_count}
        self._connection.execute(
            """
            UPDATE runs
            SET status = 'completed',
                finished_at = now(),
                metadata = metadata || %s::jsonb
            WHERE id = %s
            """,
            (Jsonb(merged), run_id),
        )

    def fail_run(self, run_id: UUID, error: str) -> None:
        self._connection.execute(
            """
            UPDATE runs
            SET status = 'failed',
                finished_at = now(),
                metadata = metadata || %s::jsonb
            WHERE id = %s
            """,
            (Jsonb({"error": error}), run_id),
        )

    def insert_observations(
        self,
        run_id: UUID,
        stream_id: UUID,
        records: list[dict[str, Any]],
        *,
        batch_size: int = 1_000,
    ) -> int:
        if not records:
            return 0

        sql = """
            INSERT INTO observations (
                run_id, stream_id, observed_at, payload, row_fingerprint
            )
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (stream_id, row_fingerprint) DO NOTHING
        """
        params = [
            (
                run_id,
                stream_id,
                record["observed_at"],
                Jsonb(record["payload"]),
                record["row_fingerprint"],
            )
            for record in records
        ]

        with self._connection.cursor() as cursor:
            for offset in range(0, len(params), batch_size):
                batch = params[offset : offset + batch_size]
                cursor.executemany(sql, batch)

        return len(records)

    def count_observations_for_stream(self, stream_id: UUID) -> int:
        row = self._connection.execute(
            "SELECT COUNT(*) AS count FROM observations WHERE stream_id = %s",
            (stream_id,),
        ).fetchone()
        assert row is not None
        return int(row["count"])

    def count_observations_for_run(self, run_id: UUID) -> int:
        row = self._connection.execute(
            "SELECT COUNT(*) AS count FROM observations WHERE run_id = %s",
            (run_id,),
        ).fetchone()
        assert row is not None
        return int(row["count"])
