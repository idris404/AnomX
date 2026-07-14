"""Enqueue alert notification jobs for ARQ workers."""

from __future__ import annotations

import asyncio
from uuid import UUID

import structlog
from arq import create_pool
from arq.connections import RedisSettings

logger = structlog.get_logger(__name__)


def _redis_settings(redis_url: str) -> RedisSettings:
    if redis_url.startswith("redis://"):
        host_port = redis_url.removeprefix("redis://").split("/", 1)[0]
        host, port_str = host_port.split(":")
        return RedisSettings(host=host, port=int(port_str))
    return RedisSettings.from_dsn(redis_url)


async def _enqueue(alert_id: UUID, redis_url: str) -> None:
    redis = await create_pool(_redis_settings(redis_url))
    try:
        await redis.enqueue_job("notify_alert", str(alert_id))
    finally:
        await redis.close()


def enqueue_alert_notification(alert_id: UUID, redis_url: str) -> None:
    asyncio.run(_enqueue(alert_id, redis_url))
    logger.info("alert_notification_enqueued", alert_id=str(alert_id))
