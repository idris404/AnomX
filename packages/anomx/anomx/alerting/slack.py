"""Slack incoming webhook alerter."""

from __future__ import annotations

from typing import Any

import httpx
import structlog

from anomx.config.models import SlackAlertingSettings

logger = structlog.get_logger(__name__)


class SlackAlerter:
    """Send compact Slack messages via incoming webhook."""

    def __init__(self, settings: SlackAlertingSettings) -> None:
        self._settings = settings

    @property
    def enabled(self) -> bool:
        return self._settings.enabled and bool(self._settings.webhook_url)

    def send(self, alert: dict[str, Any]) -> None:
        if not self.enabled:
            return
        assert self._settings.webhook_url is not None

        summary = alert.get("summary") or "Anomaly detected"
        stream = alert.get("stream", "unknown")
        score = alert.get("score")
        observed_at = alert.get("observed_at", "unknown time")
        text = (
            f":rotating_light: *AnomX alert* — `{stream}`\n"
            f"*Score*: `{score}` at `{observed_at}`\n"
            f"{summary}"
        )

        response = httpx.post(
            self._settings.webhook_url,
            json={"text": text},
            timeout=self._settings.timeout_seconds,
        )
        response.raise_for_status()
        logger.info("slack_alert_sent", alert_id=alert.get("alert_id"), status=response.status_code)
