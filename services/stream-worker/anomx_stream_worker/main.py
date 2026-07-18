"""Kafka micro-batch consumer CLI."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

import structlog

from anomx.config.loader import load_app_settings, load_source_config
from anomx.config.models import KafkaJsonSourceConfig
from anomx.ingest.stream_service import StreamIngestService
from anomx_stream_worker.paths import repo_path, repo_root

logger = structlog.get_logger(__name__)


async def run_once(
    config_path: str,
    *,
    max_messages: int,
    timeout_ms: int,
    detect_after: bool,
    settings_path: str,
    detect_config_path: str,
    group_id: str | None = None,
) -> int:
    settings = load_app_settings(repo_path(settings_path))
    source_config = load_source_config(repo_path(config_path), path_base=repo_root())
    if not isinstance(source_config, KafkaJsonSourceConfig):
        msg = f"Expected kafka_json stream config: {config_path}"
        raise TypeError(msg)
    if group_id is not None:
        source_config = source_config.model_copy(update={"group_id": group_id})

    result = await StreamIngestService(database=settings.database).consume_batch(
        source_config,
        max_messages=max_messages,
        timeout_ms=timeout_ms,
        detect_after=detect_after,
        detect_config_path=str(repo_path(detect_config_path)),
    )

    payload = result.model_dump(mode="json")
    offset_count = len(payload.get("kafka_offsets", []))
    if offset_count > 3:
        payload["kafka_offsets"] = payload["kafka_offsets"][:3]
        payload["kafka_offsets_total"] = offset_count
    print(json.dumps(payload, indent=2))  # noqa: T201

    if result.empty_batch:
        logger.warning("stream_worker_empty_batch", stream=result.stream_name)
        return 0
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Consume one Kafka micro-batch into Postgres")
    parser.add_argument(
        "--config",
        default="configs/streams/kafka_sample.yaml",
        help="Stream YAML config path (relative to repo root)",
    )
    parser.add_argument("--settings", default="config/settings.yaml")
    parser.add_argument("--detect-config", default="config/detectors.yaml")
    parser.add_argument("--max-messages", type=int, default=500)
    parser.add_argument("--timeout-ms", type=int, default=10_000)
    parser.add_argument(
        "--detect",
        action="store_true",
        help="Run DetectService after a non-empty batch",
    )
    parser.add_argument(
        "--group-id",
        default=None,
        help="Override consumer group id (use a fresh id to replay from earliest)",
    )
    args = parser.parse_args()

    try:
        raise SystemExit(
            asyncio.run(
                run_once(
                    args.config,
                    max_messages=args.max_messages,
                    timeout_ms=args.timeout_ms,
                    detect_after=args.detect,
                    settings_path=args.settings,
                    detect_config_path=args.detect_config,
                    group_id=args.group_id,
                )
            )
        )
    except KeyboardInterrupt:
        raise SystemExit(130) from None
    except Exception:
        logger.exception("stream_worker_failed")
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
