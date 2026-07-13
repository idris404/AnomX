"""Configuration models for AnomX."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class DatabaseSettings(BaseModel):
    """PostgreSQL connection settings."""

    host: str = "localhost"
    port: int = 5433
    user: str = "anomx"
    password: str = "anomx"
    db: str = "anomx"

    @property
    def dsn(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"


class CsvBatchSourceConfig(BaseModel):
    """YAML configuration for a CSV/Parquet batch source."""

    name: str = Field(min_length=1)
    source_type: Literal["csv_batch"]
    path: Path
    timestamp_column: str = Field(min_length=1)
    value_column: str = Field(min_length=1)
    format: Literal["csv", "parquet"] = "csv"
    include_columns: list[str] | None = None

    @field_validator("path")
    @classmethod
    def path_must_exist(cls, value: Path) -> Path:
        if not value.exists():
            msg = f"Source file not found: {value}"
            raise ValueError(msg)
        return value


class AppSettings(BaseModel):
    """Root application settings loaded from config/settings.yaml."""

    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
