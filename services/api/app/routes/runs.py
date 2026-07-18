"""Pipeline run history routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.dependencies import RunServiceDep
from app.schemas import RunListResponse

router = APIRouter(tags=["runs"])


@router.get("/streams/{stream_name}/runs", response_model=RunListResponse)
def list_stream_runs(
    stream_name: str,
    service: RunServiceDep,
    limit: int = Query(default=20, ge=1, le=200),
) -> RunListResponse:
    try:
        runs = service.list_runs_for_stream(stream_name, limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return RunListResponse(stream=stream_name, runs=runs)
