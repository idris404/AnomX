"""Alert notification payload builders."""

from __future__ import annotations

from typing import Any


def build_notification_payload(row: dict[str, Any]) -> dict[str, Any]:
    explanation = row.get("explanation")
    if not isinstance(explanation, dict):
        explanation = {}

    observed_at = row.get("observed_at")
    observed_str = (
        observed_at.isoformat()
        if hasattr(observed_at, "isoformat")
        else str(observed_at) if observed_at is not None else None
    )

    payload = row.get("payload")
    value = None
    if isinstance(payload, dict) and "value" in payload:
        value = payload["value"]
    elif explanation.get("value") is not None:
        value = explanation["value"]

    return {
        "alert_id": str(row["id"]),
        "stream": str(row.get("stream_name", "")),
        "score": float(row["score"]),
        "detector": str(row["detector"]),
        "observed_at": observed_str,
        "value": value,
        "summary": explanation.get("summary"),
        "rules": explanation.get("rules", []),
        "feature_contributions": explanation.get("feature_contributions", {}),
    }
