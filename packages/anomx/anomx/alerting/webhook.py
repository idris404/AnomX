"""Generic webhook alerter."""

from __future__ import annotations

from typing import Any

import httpx
import structlog

from anomx.config.models import WebhookAlertingSettings

logger = structlog.get_logger(__name__)


class WebhookAlerter:
    """POST alert payloads to a configured HTTP endpoint."""

    def __init__(self, settings: WebhookAlertingSettings) -> None:
        self._settings = settings

    @property
    def enabled(self) -> bool:
        return self._settings.enabled and bool(self._settings.url)

    def send(self, alert: dict[str, Any]) -> None:
        if not self.enabled:
            return
        assert self._settings.url is not None

        response = httpx.post(
            self._settings.url,
            json=alert,
            timeout=self._settings.timeout_seconds,
        )
        response.raise_for_status()
        logger.info("webhook_alert_sent", alert_id=alert.get("alert_id"), status=response.status_code)
