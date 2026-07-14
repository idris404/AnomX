"""Dispatch alert notifications through configured alerters."""

from __future__ import annotations

from typing import Any
from uuid import UUID

import structlog

from anomx.alerting.payload import build_notification_payload
from anomx.alerting.slack import SlackAlerter
from anomx.alerting.webhook import WebhookAlerter
from anomx.config.models import AlertingSettings, DatabaseSettings
from anomx.storage.detection import DetectionRepository
from anomx.storage.postgres import postgres_connection

logger = structlog.get_logger(__name__)


class AlertingService:
    """Loads an alert from Postgres and sends it through enabled alerters."""

    def __init__(self, database: DatabaseSettings, alerting: AlertingSettings) -> None:
        self._database = database
        self._alerters = _build_alerters(alerting)

    @property
    def has_enabled_alerters(self) -> bool:
        return any(getattr(alerter, "enabled", True) for alerter in self._alerters)

    def notify(self, alert_id: UUID) -> dict[str, Any]:
        with postgres_connection(self._database.dsn) as connection:
            repository = DetectionRepository(connection)
            row = repository.get_alert_by_id(alert_id)
            if row is None:
                msg = f"Alert not found: {alert_id}"
                raise ValueError(msg)

            payload = build_notification_payload(row)
            self._dispatch(payload)
            return payload

    def _dispatch(self, payload: dict[str, Any]) -> None:
        if not self._alerters:
            logger.warning("alert_notify_skipped_no_alerters", alert_id=payload.get("alert_id"))
            return

        for alerter in self._alerters:
            if hasattr(alerter, "enabled") and not alerter.enabled:
                continue
            alerter.send(payload)


def _build_alerters(settings: AlertingSettings) -> list[Any]:
    alerters: list[Any] = []
    webhook = WebhookAlerter(settings.webhook)
    if webhook.enabled:
        alerters.append(webhook)
    slack = SlackAlerter(settings.slack)
    if slack.enabled:
        alerters.append(slack)
    return alerters
