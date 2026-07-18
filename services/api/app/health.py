"""Dependency health checks for readiness probes."""

from __future__ import annotations

import time
from dataclasses import dataclass

import redis
from psycopg import Error as PsycopgError

from anomx.storage.postgres import postgres_connection


@dataclass(frozen=True)
class CheckResult:
    status: str
    latency_ms: float | None = None
    detail: str | None = None


def check_postgres(dsn: str) -> CheckResult:
    start = time.perf_counter()
    try:
        with postgres_connection(dsn) as connection:
            connection.execute("SELECT 1")
    except PsycopgError as exc:
        return CheckResult(status="error", detail=str(exc))
    except OSError as exc:
        return CheckResult(status="error", detail=str(exc))

    latency_ms = round((time.perf_counter() - start) * 1000, 2)
    return CheckResult(status="ok", latency_ms=latency_ms)


def check_redis(redis_url: str) -> CheckResult:
    start = time.perf_counter()
    try:
        client = redis.from_url(redis_url, socket_connect_timeout=2.0)
        client.ping()
    except redis.RedisError as exc:
        return CheckResult(status="error", detail=str(exc))
    except OSError as exc:
        return CheckResult(status="error", detail=str(exc))

    latency_ms = round((time.perf_counter() - start) * 1000, 2)
    return CheckResult(status="ok", latency_ms=latency_ms)
