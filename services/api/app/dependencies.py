"""FastAPI dependency injection."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from anomx.alerting.service import AlertingService
from anomx.alerts.service import AlertService
from anomx.config.models import AlertingSettings, DatabaseSettings
from anomx.runs.service import RunService
from app.config import Settings


def get_settings() -> Settings:
    return Settings()


SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_database_settings(settings: SettingsDep) -> DatabaseSettings:
    return settings.database_settings()


DatabaseSettingsDep = Annotated[DatabaseSettings, Depends(get_database_settings)]


def get_alerting_settings(settings: SettingsDep) -> AlertingSettings:
    return settings.alerting_settings()


AlertingSettingsDep = Annotated[AlertingSettings, Depends(get_alerting_settings)]


def get_alert_service(settings: SettingsDep) -> AlertService:
    return AlertService(database=settings.database_settings())


AlertServiceDep = Annotated[AlertService, Depends(get_alert_service)]


def get_alerting_service(settings: SettingsDep) -> AlertingService:
    return AlertingService(
        database=settings.database_settings(),
        alerting=settings.alerting_settings(),
    )


AlertingServiceDep = Annotated[AlertingService, Depends(get_alerting_service)]


def get_run_service(settings: SettingsDep) -> RunService:
    return RunService(database=settings.database_settings())


RunServiceDep = Annotated[RunService, Depends(get_run_service)]
