"""FastAPI application entry point."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from anomx import __version__ as anomx_version
from app.config import Settings
from app.health import check_postgres, check_redis
from app.metrics import HTTP_REQUEST_LATENCY_SECONDS, HTTP_REQUESTS_TOTAL
from app.routes.alerts import router as alerts_router
from app.routes.runs import router as runs_router
from app.schemas import DependencyCheck, HealthResponse, ReadinessResponse

logger = structlog.get_logger(__name__)
settings = Settings()


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    logger.info(
        "api_starting",
        app=settings.app_name,
        version=settings.app_version,
        anomx_version=anomx_version,
    )
    yield
    logger.info("api_shutdown")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

app.include_router(alerts_router)
app.include_router(runs_router)


@app.middleware("http")
async def prometheus_middleware(request: Request, call_next):  # type: ignore[no-untyped-def]
    endpoint = request.url.path
    with HTTP_REQUEST_LATENCY_SECONDS.labels(request.method, endpoint).time():
        response = await call_next(request)
    HTTP_REQUESTS_TOTAL.labels(request.method, endpoint, str(response.status_code)).inc()
    return response


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health() -> HealthResponse:
    """Liveness probe — confirms the API process is running."""
    return HealthResponse(
        status="ok",
        service="anomx-api",
        version=settings.app_version,
    )


@app.get("/health/ready", response_model=ReadinessResponse, tags=["health"])
async def health_ready() -> JSONResponse | ReadinessResponse:
    """Readiness probe — confirms Postgres and Redis are reachable."""
    postgres = check_postgres(settings.postgres_dsn)
    redis_check = check_redis(settings.redis_url)
    checks = {
        "postgres": DependencyCheck(
            status=postgres.status,
            latency_ms=postgres.latency_ms,
            detail=postgres.detail,
        ),
        "redis": DependencyCheck(
            status=redis_check.status,
            latency_ms=redis_check.latency_ms,
            detail=redis_check.detail,
        ),
    }
    all_ok = all(check.status == "ok" for check in checks.values())
    payload = ReadinessResponse(
        status="ready" if all_ok else "degraded",
        service="anomx-api",
        version=settings.app_version,
        checks=checks,
    )
    status_code = 200 if all_ok else 503
    return JSONResponse(status_code=status_code, content=payload.model_dump())


@app.get("/metrics", tags=["observability"])
async def metrics() -> Response:
    """Prometheus scrape endpoint."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
