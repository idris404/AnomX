"""Read-side alert queries for API and dashboard."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from anomx.config.models import DatabaseSettings
from anomx.storage.detection import DetectionRepository
from anomx.storage.postgres import postgres_connection


class StreamSummary(BaseModel):
    id: str
    name: str
    alert_count: int


class DetectorExplanationView(BaseModel):
    detector: str
    summary: str
    rules: list[str] = Field(default_factory=list)
    contributions: dict[str, float] = Field(default_factory=dict)


class AlertSummary(BaseModel):
    alert_id: str
    stream_name: str
    score: float
    detector: str
    observed_at: str | None
    summary: str
    rules: list[str]
    feature_contributions: dict[str, float]


class AlertDetail(AlertSummary):
    value: float | None = None
    ensemble_score: float | None = None
    ensemble_threshold: float | None = None
    detector_scores: dict[str, float] = Field(default_factory=dict)
    detectors: list[DetectorExplanationView] = Field(default_factory=list)


class AlertService:
    """Fetches streams and alerts with explanation payloads."""

    def __init__(self, database: DatabaseSettings) -> None:
        self._database = database

    def list_streams(self) -> list[StreamSummary]:
        with postgres_connection(self._database.dsn) as connection:
            repository = DetectionRepository(connection)
            rows = repository.list_streams()
            return [
                StreamSummary(
                    id=str(row["id"]),
                    name=str(row["name"]),
                    alert_count=int(row["alert_count"]),
                )
                for row in rows
            ]

    def list_alerts_for_stream(self, stream_name: str, *, limit: int = 10) -> list[AlertSummary]:
        with postgres_connection(self._database.dsn) as connection:
            repository = DetectionRepository(connection)
            stream = repository.get_stream_by_name(stream_name)
            if stream is None:
                msg = f"Stream not found: {stream_name}"
                raise ValueError(msg)

            stream_id = UUID(str(stream["id"]))
            rows = repository.list_alerts_for_stream(stream_id, limit=limit)
            return [_to_summary(row, stream_name=str(stream["name"])) for row in rows]

    def get_alert(self, alert_id: UUID) -> AlertDetail:
        with postgres_connection(self._database.dsn) as connection:
            repository = DetectionRepository(connection)
            row = repository.get_alert_by_id(alert_id)
            if row is None:
                msg = f"Alert not found: {alert_id}"
                raise ValueError(msg)
            return _to_detail(row)


def _to_summary(row: dict[str, Any], *, stream_name: str) -> AlertSummary:
    explanation = _normalize_explanation(row.get("explanation"))
    observed_at = _format_timestamp(row.get("observed_at"))

    return AlertSummary(
        alert_id=str(row["id"]),
        stream_name=stream_name,
        score=float(row["score"]),
        detector=str(row["detector"]),
        observed_at=observed_at,
        summary=str(explanation.get("summary", "No explanation available")),
        rules=[str(rule) for rule in explanation.get("rules", [])],
        feature_contributions={
            str(key): float(value)
            for key, value in (explanation.get("feature_contributions") or {}).items()
        },
    )


def _to_detail(row: dict[str, Any]) -> AlertDetail:
    stream_name = str(row["stream_name"])
    summary = _to_summary(row, stream_name=stream_name)
    explanation = _normalize_explanation(row.get("explanation"))
    payload = row.get("payload")
    value = None
    if isinstance(payload, dict) and "value" in payload:
        value = float(payload["value"])
    elif explanation.get("value") is not None:
        value = float(explanation["value"])

    detectors = []
    for item in explanation.get("detectors", []):
        if not isinstance(item, dict):
            continue
        detectors.append(
            DetectorExplanationView(
                detector=str(item.get("detector", "unknown")),
                summary=str(item.get("summary", "")),
                rules=[str(rule) for rule in item.get("rules", [])],
                contributions={
                    str(key): float(val)
                    for key, val in (item.get("contributions") or {}).items()
                },
            )
        )

    return AlertDetail(
        **summary.model_dump(),
        value=value,
        ensemble_score=_optional_float(explanation.get("ensemble_score")),
        ensemble_threshold=_optional_float(explanation.get("ensemble_threshold")),
        detector_scores={
            str(key): float(val)
            for key, val in (explanation.get("detector_scores") or {}).items()
        },
        detectors=detectors,
    )


def _normalize_explanation(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    return {}


def _format_timestamp(value: Any) -> str | None:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)
