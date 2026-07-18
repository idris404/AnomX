"""FastAPI application entry point."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from anomx import __version__ as anomx_version
from app.config import Settings
from app.metrics import HTTP_REQUEST_LATENCY_SECONDS, HTTP_REQUESTS_TOTAL
from app.routes.alerts import router as alerts_router
from app.routes.runs import router as runs_router
from app.schemas import HealthResponse

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


@app.get("/metrics", tags=["observability"])
async def metrics() -> Response:
    """Prometheus scrape endpoint."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
