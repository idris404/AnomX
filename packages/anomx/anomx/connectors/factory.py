"""Source connector factory."""

from __future__ import annotations

from typing import Any

from anomx.config.models import (
    CsvBatchSourceConfig,
    DatabaseSettings,
    KafkaJsonSourceConfig,
    NabBatchSourceConfig,
    OnlineRetailBatchSourceConfig,
    PostgresQuerySourceConfig,
    SourceConfig,
)
from anomx.connectors.csv_batch import CsvBatchSource
from anomx.connectors.kafka_json import KafkaJsonSource
from anomx.connectors.nab_batch import NabBatchSource
from anomx.connectors.online_retail import OnlineRetailBatchSource
from anomx.connectors.postgres_query import PostgresQuerySource


def build_source(config: SourceConfig, *, database: DatabaseSettings | None = None) -> Any:
    if isinstance(config, CsvBatchSourceConfig):
        return CsvBatchSource(
            path=config.path,
            timestamp_column=config.timestamp_column,
            value_column=config.value_column,
            file_format=config.format,
            include_columns=config.include_columns,
        )
    if isinstance(config, NabBatchSourceConfig):
        return NabBatchSource(
            path=config.path,
            dataset_name=config.dataset_name,
            timestamp_column=config.timestamp_column,
            value_column=config.value_column,
            labels_path=config.labels_path,
            labels_key=config.labels_key,
        )
    if isinstance(config, OnlineRetailBatchSourceConfig):
        return OnlineRetailBatchSource(
            path=config.path,
            timestamp_column=config.timestamp_column,
            quantity_column=config.quantity_column,
            price_column=config.price_column,
            aggregate=config.aggregate,
        )
    if isinstance(config, PostgresQuerySourceConfig):
        if database is None:
            msg = "PostgresQuerySource requires database settings"
            raise ValueError(msg)
        return PostgresQuerySource(
            database=database,
            query=config.query,
            timestamp_column=config.timestamp_column,
            value_column=config.value_column,
        )
    if isinstance(config, KafkaJsonSourceConfig):
        return KafkaJsonSource(
            bootstrap_servers=config.bootstrap_servers,
            topic=config.topic,
            group_id=config.group_id,
            timestamp_field=config.timestamp_field,
            value_field=config.value_field,
            auto_offset_reset=config.auto_offset_reset,
        )
    msg = f"Unsupported source config: {config!r}"
    raise ValueError(msg)
