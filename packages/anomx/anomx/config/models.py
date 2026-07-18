"""Configuration models for AnomX."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Literal

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


class WebhookAlertingSettings(BaseModel):
    """Generic HTTP webhook alerter."""

    enabled: bool = False
    url: str | None = None
    timeout_seconds: float = 10.0


class SlackAlertingSettings(BaseModel):
    """Slack incoming webhook alerter."""

    enabled: bool = False
    webhook_url: str | None = None
    timeout_seconds: float = 10.0


class AlertingSettings(BaseModel):
    """Outbound alert notification settings."""

    webhook: WebhookAlertingSettings = Field(default_factory=WebhookAlertingSettings)
    slack: SlackAlertingSettings = Field(default_factory=SlackAlertingSettings)


class MlflowSettings(BaseModel):
    """MLflow experiment tracking settings (Phase 9)."""

    enabled: bool = False
    tracking_uri: str = "sqlite:///mlruns/mlflow.db"
    experiment_name: str = "anomx-detect"


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


class NabBatchSourceConfig(BaseModel):
    """YAML configuration for a NAB labeled CSV source."""

    name: str = Field(min_length=1)
    source_type: Literal["nab_batch"]
    path: Path
    dataset_name: str = Field(min_length=1)
    timestamp_column: str = "timestamp"
    value_column: str = "value"
    labels_path: Path | None = None
    labels_key: str | None = None

    @field_validator("path")
    @classmethod
    def path_must_exist(cls, value: Path) -> Path:
        if not value.exists():
            msg = f"Source file not found: {value}"
            raise ValueError(msg)
        return value


class OnlineRetailBatchSourceConfig(BaseModel):
    """YAML configuration for Online Retail II daily aggregation."""

    name: str = Field(min_length=1)
    source_type: Literal["online_retail_batch"]
    path: Path
    timestamp_column: str = "InvoiceDate"
    quantity_column: str = "Quantity"
    price_column: str = "UnitPrice"
    aggregate: Literal["daily_revenue", "daily_quantity"] = "daily_revenue"

    @field_validator("path")
    @classmethod
    def path_must_exist(cls, value: Path) -> Path:
        if not value.exists():
            msg = f"Source file not found: {value}"
            raise ValueError(msg)
        return value


class PostgresQuerySourceConfig(BaseModel):
    """YAML configuration for a PostgreSQL snapshot query source."""

    name: str = Field(min_length=1)
    source_type: Literal["postgres_query"]
    query: str = Field(min_length=1)
    timestamp_column: str = Field(min_length=1)
    value_column: str = Field(min_length=1)


class KafkaJsonSourceConfig(BaseModel):
    """YAML configuration for a Kafka/Redpanda JSON topic consumer."""

    name: str = Field(min_length=1)
    source_type: Literal["kafka_json"]
    bootstrap_servers: str = "127.0.0.1:19092"
    topic: str = Field(min_length=1)
    group_id: str = "anomx-ingest"
    timestamp_field: str = "timestamp"
    value_field: str = "value"
    auto_offset_reset: Literal["earliest", "latest"] = "earliest"


SourceConfig = Annotated[
    CsvBatchSourceConfig
    | NabBatchSourceConfig
    | OnlineRetailBatchSourceConfig
    | PostgresQuerySourceConfig
    | KafkaJsonSourceConfig,
    Field(discriminator="source_type"),
]


class AppSettings(BaseModel):
    """Root application settings loaded from config/settings.yaml."""

    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    alerting: AlertingSettings = Field(default_factory=AlertingSettings)
    mlflow: MlflowSettings = Field(default_factory=MlflowSettings)
