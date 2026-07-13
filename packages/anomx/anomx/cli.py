"""CLI entry point for AnomX (Phase 0 stub)."""

from __future__ import annotations

import argparse
import sys

import structlog

from anomx import __version__

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

    parser.print_help()
    return 0 if args.command is None else 1


if __name__ == "__main__":
    sys.exit(main())
