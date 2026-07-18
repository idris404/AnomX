"""Kafka/Redpanda JSON topic source connector."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any, Literal

import structlog
from aiokafka import AIOKafkaConsumer

from anomx.connectors.common import coerce_timestamp

logger = structlog.get_logger(__name__)


class KafkaJsonSource:
    """Consumes JSON observation messages from a Kafka-compatible topic."""

    def __init__(
        self,
        bootstrap_servers: str,
        topic: str,
        *,
        group_id: str,
        timestamp_field: str,
        value_field: str,
        auto_offset_reset: Literal["earliest", "latest"] = "earliest",
    ) -> None:
        self._bootstrap_servers = bootstrap_servers
        self._topic = topic
        self._group_id = group_id
        self._timestamp_field = timestamp_field
        self._value_field = value_field
        self._auto_offset_reset = auto_offset_reset
        self._consumer: AIOKafkaConsumer | None = None

    async def poll_batch(
        self,
        *,
        max_messages: int = 500,
        timeout_ms: int = 5_000,
    ) -> tuple[list[dict[str, Any]], list[dict[str, int | str]]]:
        consumer = await self._ensure_consumer()
        batches = await consumer.getmany(timeout_ms=timeout_ms, max_records=max_messages)

        records: list[dict[str, Any]] = []
        offsets: list[dict[str, int | str]] = []
        for partition_messages in batches.values():
            for message in partition_messages:
                payload = message.value
                if not isinstance(payload, dict):
                    msg = f"Expected JSON object in Kafka message, got {type(payload)!r}"
                    raise ValueError(msg)
                records.append(
                    parse_kafka_json_message(
                        payload,
                        timestamp_field=self._timestamp_field,
                        value_field=self._value_field,
                        topic=message.topic,
                        partition=message.partition,
                        offset=message.offset,
                    )
                )
                offsets.append(
                    {
                        "topic": message.topic,
                        "partition": message.partition,
                        "offset": message.offset,
                    }
                )
                if len(records) >= max_messages:
                    break
            if len(records) >= max_messages:
                break

        logger.info(
            "kafka_json_poll_complete",
            topic=self._topic,
            records=len(records),
        )
        return records, offsets

    async def commit(self) -> None:
        if self._consumer is not None:
            await self._consumer.commit()

    async def close(self) -> None:
        if self._consumer is not None:
            await self._consumer.stop()
            self._consumer = None

    async def _ensure_consumer(self) -> AIOKafkaConsumer:
        if self._consumer is None:
            self._consumer = AIOKafkaConsumer(
                self._topic,
                bootstrap_servers=self._bootstrap_servers,
                group_id=self._group_id,
                auto_offset_reset=self._auto_offset_reset,
                enable_auto_commit=False,
                value_deserializer=lambda raw: json.loads(raw.decode("utf-8")),
            )
            await self._consumer.start()
        return self._consumer


def parse_kafka_json_message(
    payload: dict[str, Any],
    *,
    timestamp_field: str,
    value_field: str,
    topic: str,
    partition: int,
    offset: int,
) -> dict[str, Any]:
    if timestamp_field not in payload:
        msg = f"Missing timestamp field in Kafka message: {timestamp_field}"
        raise ValueError(msg)
    if value_field not in payload:
        msg = f"Missing value field in Kafka message: {value_field}"
        raise ValueError(msg)

    observed_at = parse_timestamp(payload[timestamp_field])
    value = float(payload[value_field])
    observation_payload = {
        key: json_safe(value_item)
        for key, value_item in payload.items()
        if key not in {timestamp_field, value_field}
    }
    observation_payload[value_field] = value
    observation_payload["kafka"] = {
        "topic": topic,
        "partition": partition,
        "offset": offset,
    }
    return {"observed_at": observed_at, "payload": observation_payload}


def parse_timestamp(value: Any) -> datetime:
    if isinstance(value, datetime):
        return coerce_timestamp(value)
    if isinstance(value, str):
        normalized = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
        return coerce_timestamp(parsed)
    msg = f"Unsupported timestamp value: {value!r}"
    raise ValueError(msg)


def json_safe(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat()
    return value
