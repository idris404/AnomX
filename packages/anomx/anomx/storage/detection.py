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
    ) -> tuple[bool, UUID]:
        dedupe_key = f"{stream_id}:{observation_id}:{detector}"
        row = self._connection.execute(
            """
            INSERT INTO alerts (
                run_id, stream_id, observation_id, score, detector, explanation, dedupe_key
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (dedupe_key) WHERE dedupe_key IS NOT NULL DO UPDATE SET
                run_id = EXCLUDED.run_id,
                score = EXCLUDED.score,
                explanation = EXCLUDED.explanation
            RETURNING id, (xmax = 0) AS inserted
            """,
            (run_id, stream_id, observation_id, score, detector, Jsonb(explanation), dedupe_key),
        ).fetchone()
        assert row is not None
        return bool(row["inserted"]), UUID(str(row["id"]))

    def list_streams(self) -> list[dict[str, Any]]:
        rows = self._connection.execute(
            """
            SELECT
                s.id,
                s.name,
                COUNT(a.id) AS alert_count
            FROM streams s
            LEFT JOIN alerts a ON a.stream_id = s.id
            GROUP BY s.id, s.name
            ORDER BY s.name ASC
            """,
        ).fetchall()
        return [dict(row) for row in rows]

    def get_alert_by_id(self, alert_id: UUID) -> dict[str, Any] | None:
        row = self._connection.execute(
            """
            SELECT
                a.id,
                a.run_id,
                a.stream_id,
                a.observation_id,
                a.score,
                a.detector,
                a.explanation,
                a.created_at,
                s.name AS stream_name,
                o.observed_at,
                o.payload
            FROM alerts a
            JOIN streams s ON s.id = a.stream_id
            LEFT JOIN observations o ON o.id = a.observation_id
            WHERE a.id = %s
            """,
            (alert_id,),
        ).fetchone()
        return dict(row) if row is not None else None

    def count_alerts_for_run(self, run_id: UUID) -> int:
        row = self._connection.execute(
            "SELECT COUNT(*) AS count FROM alerts WHERE run_id = %s",
            (run_id,),
        ).fetchone()
        assert row is not None
        return int(row["count"])

    def list_alerts_for_stream(self, stream_id: UUID, *, limit: int = 10) -> list[dict[str, Any]]:
        rows = self._connection.execute(
            """
            SELECT
                a.id,
                a.score,
                a.detector,
                a.explanation,
                a.created_at,
                o.observed_at,
                o.payload
            FROM alerts a
            LEFT JOIN observations o ON o.id = a.observation_id
            WHERE a.stream_id = %s
            ORDER BY a.created_at DESC
            LIMIT %s
            """,
            (stream_id, limit),
        ).fetchall()
        return [dict(row) for row in rows]
