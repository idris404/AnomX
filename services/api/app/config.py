"""Application settings."""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from anomx.config.loader import load_app_settings
from anomx.config.models import AlertingSettings, DatabaseSettings


class Settings(BaseSettings):
    """Environment-driven configuration for the API service."""

    model_config = SettingsConfigDict(env_prefix="ANOMX_", env_file=".env", extra="ignore")

    app_name: str = "AnomX API"
    app_version: str = "0.1.0"
    debug: bool = False
    settings_path: Path = Path("config/settings.yaml")

    postgres_host: str = "localhost"
    postgres_port: int = 5433
    postgres_user: str = "anomx"
    postgres_password: str = "anomx"
    postgres_db: str = "anomx"

    redis_host: str = "localhost"
    redis_port: int = 6379

    @property
    def postgres_dsn(self) -> str:
        return self.database_settings().dsn

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/0"

    def database_settings(self) -> DatabaseSettings:
        if self.settings_path.exists():
            return load_app_settings(self.settings_path).database
        return DatabaseSettings(
            host=self.postgres_host,
            port=self.postgres_port,
            user=self.postgres_user,
            password=self.postgres_password,
            db=self.postgres_db,
        )

    def alerting_settings(self) -> AlertingSettings:
        if self.settings_path.exists():
            return load_app_settings(self.settings_path).alerting
        return AlertingSettings()
