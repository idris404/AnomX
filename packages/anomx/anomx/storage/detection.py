"""PostgreSQL persistence for anomaly detection runs."""

from __future__ import annotations

from typing import Any
from uuid import UUID

import psycopg
from psycopg.types.json import Jsonb


class DetectionRepository:
    """Reads observations and writes scores/alerts."""

    def __init__(self, connection: psycopg.Connection[Any]) -> None:
        self._connection = connection

    def get_stream_by_name(self, name: str) -> dict[str, Any] | None:
        return self._connection.execute(
            "SELECT id, name FROM streams WHERE name = %s",
            (name,),
        ).fetchone()

    def get_latest_ingestion_run(self, stream_id: UUID) -> dict[str, Any] | None:
        return self._connection.execute(
            """
            SELECT id, metadata
            FROM runs
            WHERE stream_id = %s
              AND status = 'completed'
              AND metadata ? 'content_hash'
            ORDER BY finished_at DESC NULLS LAST, started_at DESC
            LIMIT 1
            """,
            (stream_id,),
        ).fetchone()

    def fetch_observations(self, stream_id: UUID, run_id: UUID) -> list[dict[str, Any]]:
        rows = self._connection.execute(
            """
            SELECT id, observed_at, payload
            FROM observations
            WHERE stream_id = %s AND run_id = %s
            ORDER BY observed_at ASC, id ASC
            """,
            (stream_id, run_id),
        ).fetchall()

        records: list[dict[str, Any]] = []
        for row in rows:
            payload = row["payload"]
            if not isinstance(payload, dict):
                payload = {}
            record: dict[str, Any] = {
                "observation_id": int(row["id"]),
                "observed_at": row["observed_at"],
                **payload,
            }
            records.append(record)
        return records

    def create_detection_run(
        self,
        stream_id: UUID,
        source_run_id: UUID,
        metadata: dict[str, Any],
    ) -> UUID:
        row = self._connection.execute(
            """
            INSERT INTO runs (stream_id, status, metadata)
            VALUES (%s, 'running', %s)
            RETURNING id
            """,
            (stream_id, Jsonb({**metadata, "run_type": "detection"})),
        ).fetchone()
        assert row is not None
        return UUID(str(row["id"]))

    def complete_detection_run(self, run_id: UUID, metadata: dict[str, Any]) -> None:
        self._connection.execute(
            """
            UPDATE runs
            SET status = 'completed',
                finished_at = now(),
                metadata = metadata || %s::jsonb
            WHERE id = %s
            """,
            (Jsonb(metadata), run_id),
        )

    def fail_detection_run(self, run_id: UUID, error: str) -> None:
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

    def insert_scores(
        self,
        run_id: UUID,
        observation_id: int,
        detector: str,
        score: float,
        is_anomaly: bool,
    ) -> None:
        self._connection.execute(
            """
            INSERT INTO scores (run_id, observation_id, detector, score, is_anomaly)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (run_id, observation_id, detector, score, is_anomaly),
        )

    def insert_alert(
        self,
        run_id: UUID,
        stream_id: UUID,
        observation_id: int,
        score: float,
        detector: str,
        explanation: dict[str, Any],
    ) -> None:
        dedupe_key = f"{stream_id}:{observation_id}:{detector}"
        self._connection.execute(
            """
            INSERT INTO alerts (
                run_id, stream_id, observation_id, score, detector, explanation, dedupe_key
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (dedupe_key) WHERE dedupe_key IS NOT NULL DO NOTHING
            """,
            (run_id, stream_id, observation_id, score, detector, Jsonb(explanation), dedupe_key),
        )

    def count_alerts_for_run(self, run_id: UUID) -> int:
        row = self._connection.execute(
            "SELECT COUNT(*) AS count FROM alerts WHERE run_id = %s",
            (run_id,),
        ).fetchone()
        assert row is not None
        return int(row["count"])
