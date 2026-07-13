"""CLI entry point for AnomX."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import structlog

from anomx import __version__
from anomx.config.loader import (
    load_app_settings,
    load_benchmark_config,
    load_csv_source_config,
    load_detect_config,
)
from anomx.benchmark.runner import BenchmarkRunner
from anomx.detect.service import DetectService
from anomx.explain.service import ExplainService
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

    detect_parser = subparsers.add_parser("detect", help="Run anomaly detection on a stream")
    detect_parser.add_argument(
        "--stream",
        required=True,
        help="Stream name (must match a previously ingested source)",
    )
    detect_parser.add_argument(
        "--config",
        type=Path,
        default=Path("config/detectors.yaml"),
        help="Path to detector YAML config",
    )
    detect_parser.add_argument(
        "--settings",
        type=Path,
        default=Path("config/settings.yaml"),
        help="Path to app settings YAML (database connection)",
    )

    benchmark_parser = subparsers.add_parser("benchmark", help="Run reproducible detector benchmark")
    benchmark_parser.add_argument(
        "--config",
        type=Path,
        default=Path("config/benchmark.yaml"),
        help="Path to benchmark YAML config",
    )

    explain_parser = subparsers.add_parser("explain", help="Show alert explanations for a stream")
    explain_parser.add_argument(
        "--stream",
        required=True,
        help="Stream name",
    )
    explain_parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Maximum number of alerts to display",
    )
    explain_parser.add_argument(
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

    if args.command == "detect":
        return _run_detect(args.stream, args.config, args.settings)

    if args.command == "benchmark":
        return _run_benchmark(args.config)

    if args.command == "explain":
        return _run_explain(args.stream, args.limit, args.settings)

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


def _run_detect(stream_name: str, config_path: Path, settings_path: Path) -> int:
    detect_config = load_detect_config(config_path)
    app_settings = load_app_settings(settings_path)
    service = DetectService(database=app_settings.database)
    result = service.detect_stream(stream_name, detect_config)

    payload = {
        "run_id": str(result.run_id),
        "stream_id": str(result.stream_id),
        "stream_name": result.stream_name,
        "source_run_id": str(result.source_run_id),
        "observations_scored": result.observations_scored,
        "alerts_created": result.alerts_created,
        "ensemble_threshold": result.ensemble_threshold,
    }
    print(json.dumps(payload, indent=2))  # noqa: T201
    return 0


def _run_benchmark(config_path: Path) -> int:
    benchmark_config = load_benchmark_config(config_path)
    result = BenchmarkRunner(benchmark_config).run()

    payload = {
        "seed": result.seed,
        "dataset_type": result.dataset_type,
        "n_samples": result.n_samples,
        "n_anomalies": result.n_anomalies,
        "report_json": str(result.report_json),
        "report_markdown": str(result.report_markdown),
        "detectors": [
            {
                "name": detector.name,
                "precision": detector.precision,
                "recall": detector.recall,
                "f1": detector.f1,
                "false_positives_per_hour": detector.false_positives_per_hour,
            }
            for detector in result.detectors
        ],
    }
    print(json.dumps(payload, indent=2))  # noqa: T201
    return 0


def _run_explain(stream_name: str, limit: int, settings_path: Path) -> int:
    app_settings = load_app_settings(settings_path)
    views = ExplainService(database=app_settings.database).list_alert_explanations(
        stream_name,
        limit=limit,
    )
    payload = [view.model_dump() for view in views]
    print(json.dumps(payload, indent=2))  # noqa: T201
    return 0


if __name__ == "__main__":
    sys.exit(main())
