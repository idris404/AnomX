"""Read and display alert explanations."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel

from anomx.config.models import DatabaseSettings
from anomx.storage.detection import DetectionRepository
from anomx.storage.postgres import postgres_connection


class AlertExplanationView(BaseModel):
    alert_id: str
    score: float
    detector: str
    observed_at: str | None
    summary: str
    rules: list[str]
    feature_contributions: dict[str, float]


class ExplainService:
    """Fetches stored explanations for a stream's alerts."""

    def __init__(self, database: DatabaseSettings) -> None:
        self._database = database

    def list_alert_explanations(
        self,
        stream_name: str,
        *,
        limit: int = 10,
    ) -> list[AlertExplanationView]:
        with postgres_connection(self._database.dsn) as connection:
            repository = DetectionRepository(connection)
            stream = repository.get_stream_by_name(stream_name)
            if stream is None:
                msg = f"Stream not found: {stream_name}"
                raise ValueError(msg)

            stream_id = UUID(str(stream["id"]))
            rows = repository.list_alerts_for_stream(stream_id, limit=limit)
            return [_to_view(row) for row in rows]


def _to_view(row: dict[str, Any]) -> AlertExplanationView:
    explanation = row.get("explanation") or {}
    if not isinstance(explanation, dict):
        explanation = {}

    observed_at = row.get("observed_at")
    observed_str = (
        observed_at.isoformat()
        if hasattr(observed_at, "isoformat")
        else str(observed_at) if observed_at is not None else None
    )

    return AlertExplanationView(
        alert_id=str(row["id"]),
        score=float(row["score"]),
        detector=str(row["detector"]),
        observed_at=observed_str,
        summary=str(explanation.get("summary", "No explanation available")),
        rules=[str(rule) for rule in explanation.get("rules", [])],
        feature_contributions={
            str(key): float(value)
            for key, value in (explanation.get("feature_contributions") or {}).items()
        },
    )
