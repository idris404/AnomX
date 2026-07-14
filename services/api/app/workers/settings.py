"""ARQ worker configuration."""

from __future__ import annotations

from arq.connections import RedisSettings

from app.config import Settings
from app.workers.tasks import notify_alert

_settings = Settings()


class WorkerSettings:
    functions = [notify_alert]
    redis_settings = RedisSettings(host=_settings.redis_host, port=_settings.redis_port)
