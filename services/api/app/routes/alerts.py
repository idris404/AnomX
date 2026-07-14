"""Alert read and notification routes."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from app.dependencies import AlertingServiceDep, AlertServiceDep, SettingsDep
from app.schemas import AlertListResponse, AlertResponse, NotifyResponse, StreamListResponse
from app.workers.enqueue import enqueue_alert_notification

router = APIRouter(tags=["alerts"])


@router.get("/streams", response_model=StreamListResponse)
def list_streams(service: AlertServiceDep) -> StreamListResponse:
    return StreamListResponse(streams=service.list_streams())


@router.get("/streams/{stream_name}/alerts", response_model=AlertListResponse)
def list_stream_alerts(
    stream_name: str,
    service: AlertServiceDep,
    limit: int = Query(default=20, ge=1, le=200),
) -> AlertListResponse:
    try:
        alerts = service.list_alerts_for_stream(stream_name, limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return AlertListResponse(stream=stream_name, alerts=alerts)


@router.get("/alerts/{alert_id}", response_model=AlertResponse)
def get_alert(
    alert_id: UUID,
    service: AlertServiceDep,
) -> AlertResponse:
    try:
        alert = service.get_alert(alert_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return AlertResponse(alert=alert)


@router.post("/alerts/{alert_id}/notify", response_model=NotifyResponse)
def notify_alert(
    alert_id: UUID,
    alert_service: AlertServiceDep,
    alerting_service: AlertingServiceDep,
    settings: SettingsDep,
    async_dispatch: Annotated[bool, Query(alias="async")] = True,
) -> NotifyResponse:
    try:
        alert_service.get_alert(alert_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    if async_dispatch:
        enqueue_alert_notification(alert_id, settings.redis_url)
        return NotifyResponse(
            alert_id=str(alert_id),
            queued=True,
            message="Alert notification queued",
        )

    if not alerting_service.has_enabled_alerters:
        raise HTTPException(status_code=400, detail="No alerting channels are enabled")

    alerting_service.notify(alert_id)
    return NotifyResponse(
        alert_id=str(alert_id),
        queued=False,
        message="Alert notification sent",
    )
