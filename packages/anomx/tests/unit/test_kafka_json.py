"""Unit tests for Kafka JSON message parsing."""

from datetime import UTC, datetime

import pytest

from anomx.connectors.kafka_json import parse_kafka_json_message, parse_timestamp


def test_parse_kafka_json_message_maps_observation() -> None:
    record = parse_kafka_json_message(
        {
            "timestamp": "2024-01-01T00:00:00+00:00",
            "value": 42.5,
            "source": "sample_csv",
        },
        timestamp_field="timestamp",
        value_field="value",
        topic="anomx.observations",
        partition=0,
        offset=12,
    )

    assert record["observed_at"] == datetime(2024, 1, 1, tzinfo=UTC)
    assert record["payload"]["value"] == 42.5
    assert record["payload"]["source"] == "sample_csv"
    assert record["payload"]["kafka"]["offset"] == 12


def test_parse_timestamp_rejects_unknown_type() -> None:
    with pytest.raises(ValueError, match="Unsupported timestamp"):
        parse_timestamp(12345)
