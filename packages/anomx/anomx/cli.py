"""CLI entry point for AnomX."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import structlog

from anomx import __version__
from anomx.config.loader import load_app_settings, load_csv_source_config
from anomx.ingest.service import IngestService

logger = structlog.get_logger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="anomx",
        description="AnomX — pluggable anomaly detection engine",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("info", help="Show package info")

    ingest_parser = subparsers.add_parser("ingest", help="Ingest a batch CSV/Parquet source")
    ingest_parser.add_argument(
        "--config",
        required=True,
        type=Path,
        help="Path to source YAML config (e.g. config/sources/sample_csv.yaml)",
    )
    ingest_parser.add_argument(
        "--settings",
        type=Path,
        default=Path("config/settings.yaml"),
        help="Path to app settings YAML (database connection)",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(),
        ],
    )

    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "info":
        logger.info("anomx_ready", version=__version__)
        return 0

    if args.command == "ingest":
        return _run_ingest(args.config, args.settings)

    parser.print_help()
    return 0 if args.command is None else 1


def _run_ingest(config_path: Path, settings_path: Path) -> int:
    source_config = load_csv_source_config(config_path)
    app_settings = load_app_settings(settings_path)
    service = IngestService(database=app_settings.database)
    result = service.ingest_csv_batch(source_config)

    payload = {
        "run_id": str(result.run_id),
        "stream_id": str(result.stream_id),
        "stream_name": result.stream_name,
        "records_read": result.records_read,
        "records_written": result.records_written,
        "content_hash": result.content_hash,
        "skipped": result.skipped,
    }
    print(json.dumps(payload, indent=2))  # noqa: T201
    return 0


if __name__ == "__main__":
    sys.exit(main())
