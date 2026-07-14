"""ARQ worker tasks."""

from __future__ import annotations

from uuid import UUID

import structlog

from anomx.alerting.service import AlertingService
from app.config import Settings

logger = structlog.get_logger(__name__)


async def notify_alert(_ctx: dict[str, object], alert_id: str) -> dict[str, str]:
    settings = Settings()
    service = AlertingService(
        database=settings.database_settings(),
        alerting=settings.alerting_settings(),
    )
    if not service.has_enabled_alerters:
        logger.warning("notify_alert_skipped_no_alerters", alert_id=alert_id)
        return {"status": "skipped", "reason": "no alerters enabled"}

    payload = service.notify(UUID(alert_id))
    logger.info("notify_alert_complete", alert_id=alert_id)
    return {"status": "sent", "alert_id": payload["alert_id"]}
