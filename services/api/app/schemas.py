"""Pydantic schemas for API responses."""

from __future__ import annotations

from pydantic import BaseModel, Field

from anomx.alerts.service import AlertDetail, AlertSummary, StreamSummary
from anomx.runs.service import RunSummary


class HealthResponse(BaseModel):
    """Health check payload."""

    status: str = Field(examples=["ok"])
    service: str = Field(examples=["anomx-api"])
    version: str = Field(examples=["0.1.0"])


class StreamListResponse(BaseModel):
    streams: list[StreamSummary]


class AlertListResponse(BaseModel):
    stream: str
    alerts: list[AlertSummary]


class NotifyResponse(BaseModel):
    alert_id: str
    queued: bool
    message: str


class AlertResponse(BaseModel):
    alert: AlertDetail


class RunListResponse(BaseModel):
    stream: str
    runs: list[RunSummary]
