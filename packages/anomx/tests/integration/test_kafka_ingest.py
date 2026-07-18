"""Integration tests for Kafka stream ingestion."""

from __future__ import annotations

import asyncio
import json
import socket
from pathlib import Path
from uuid import uuid4

import psycopg
import pytest
from aiokafka import AIOKafkaProducer

from anomx.config.models import DatabaseSettings, KafkaJsonSourceConfig
from anomx.ingest.stream_service import StreamIngestService
from tests.helpers import cleanup_stream, generate_timeseries_csv


def kafka_available(bootstrap_servers: str = "127.0.0.1:19092") -> bool:
    host, port_str = bootstrap_servers.rsplit(":", 1)
    try:
        with socket.create_connection((host, int(port_str)), timeout=1):
            return True
    except OSError:
        return False


@pytest.fixture
def require_kafka() -> str:
    bootstrap = "127.0.0.1:19092"
    if not kafka_available(bootstrap):
        pytest.skip("Redpanda is not available on 127.0.0.1:19092")
    return bootstrap


async def _publish_csv(
    csv_path: Path,
    *,
    bootstrap_servers: str,
    topic: str,
) -> None:
    rows = csv_path.read_text(encoding="utf-8").strip().splitlines()[1:]
    producer = AIOKafkaProducer(
        bootstrap_servers=bootstrap_servers,
        value_serializer=lambda value: json.dumps(value).encode("utf-8"),
    )
    await producer.start()
    try:
        for line in rows:
            timestamp, value = line.split(",")
            await producer.send_and_wait(
                topic,
                {"timestamp": timestamp, "value": float(value)},
            )
    finally:
        await producer.stop()


@pytest.mark.integration
def test_stream_ingest_from_kafka(
    require_kafka: str,
    require_postgres: str,
    tmp_path: Path,
) -> None:
    stream_name = f"test_kafka_{uuid4().hex[:8]}"
    topic = f"anomx.test.{uuid4().hex[:8]}"
    csv_path = tmp_path / "kafka_source.csv"
    generate_timeseries_csv(csv_path, rows=50)

    asyncio.run(
        _publish_csv(
            csv_path,
            bootstrap_servers=require_kafka,
            topic=topic,
        )
    )

    config = KafkaJsonSourceConfig(
        name=stream_name,
        source_type="kafka_json",
        bootstrap_servers=require_kafka,
        topic=topic,
        group_id=f"anomx-test-{uuid4().hex[:8]}",
    )
    settings = DatabaseSettings()

    try:
        result = asyncio.run(
            StreamIngestService(database=settings).consume_batch(
                config,
                max_messages=100,
                timeout_ms=10_000,
            )
        )
        assert result.empty_batch is False
        assert result.records_read == 50
        assert result.records_written == 50
    finally:
        with psycopg.connect(require_postgres) as connection:
            cleanup_stream(connection, stream_name)
