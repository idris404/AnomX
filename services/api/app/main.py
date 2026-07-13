"""FastAPI application entry point."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI

from anomx import __version__ as anomx_version
from app.config import Settings
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


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health() -> HealthResponse:
    """Liveness probe — confirms the API process is running."""
    return HealthResponse(
        status="ok",
        service="anomx-api",
        version=settings.app_version,
    )
