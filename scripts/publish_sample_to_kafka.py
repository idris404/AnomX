"""Publish sample CSV rows to Kafka/Redpanda as JSON events."""

from __future__ import annotations

import argparse
import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path

import polars as pl
from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaConnectionError


async def publish_csv_to_kafka(
    csv_path: Path,
    *,
    bootstrap_servers: str,
    topic: str,
    timestamp_column: str,
    value_column: str,
    max_retries: int = 30,
    retry_delay_seconds: float = 2.0,
) -> int:
    frame = pl.read_csv(csv_path, try_parse_dates=True)
    producer: AIOKafkaProducer | None = None

    for attempt in range(max_retries):
        try:
            producer = AIOKafkaProducer(
                bootstrap_servers=bootstrap_servers,
                value_serializer=lambda value: json.dumps(value, default=str).encode("utf-8"),
            )
            await producer.start()
            break
        except KafkaConnectionError:
            if producer is not None:
                await producer.stop()
            if attempt + 1 >= max_retries:
                raise
            await asyncio.sleep(retry_delay_seconds)

    assert producer is not None
    sent = 0
    try:
        for row in frame.iter_rows(named=True):
            timestamp = row[timestamp_column]
            if isinstance(timestamp, datetime):
                if timestamp.tzinfo is None:
                    timestamp = timestamp.replace(tzinfo=UTC)
                else:
                    timestamp = timestamp.astimezone(UTC)
                timestamp_str = timestamp.isoformat()
            else:
                timestamp_str = str(timestamp)

            payload = {
                timestamp_column: timestamp_str,
                value_column: float(row[value_column]),
                "source": "sample_csv",
            }
            await producer.send_and_wait(topic, payload)
            sent += 1
    finally:
        await producer.stop()

    return sent


def main() -> None:
    parser = argparse.ArgumentParser(description="Publish sample CSV rows to Kafka/Redpanda")
    parser.add_argument(
        "--csv",
        type=Path,
        default=Path("data/samples/example.csv"),
        help="CSV file to publish",
    )
    parser.add_argument(
        "--bootstrap-servers",
        default="127.0.0.1:19092",
        help="Kafka bootstrap servers",
    )
    parser.add_argument("--topic", default="anomx.observations", help="Target topic")
    parser.add_argument("--timestamp-column", default="timestamp")
    parser.add_argument("--value-column", default="value")
    args = parser.parse_args()

    if not args.csv.is_file():
        msg = f"CSV file not found: {args.csv}"
        raise SystemExit(msg)

    sent = asyncio.run(
        publish_csv_to_kafka(
            args.csv,
            bootstrap_servers=args.bootstrap_servers,
            topic=args.topic,
            timestamp_column=args.timestamp_column,
            value_column=args.value_column,
        )
    )
    print(f"Published {sent} messages to topic {args.topic}")  # noqa: T201


if __name__ == "__main__":
    main()
