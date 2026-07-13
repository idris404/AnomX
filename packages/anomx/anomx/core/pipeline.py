"""Pipeline orchestration (Phase 0 stub)."""

from __future__ import annotations

from typing import Any

import structlog

from anomx.core.interfaces import Sink, Source

logger = structlog.get_logger(__name__)


class Pipeline:
    """Minimal ingest pipeline: source → sink."""

    def __init__(self, source: Source, sink: Sink) -> None:
        self._source = source
        self._sink = sink

    def run(self) -> dict[str, Any]:
        """Execute a single pipeline pass."""
        records = self._source.read()
        count = self._sink.write(records)
        logger.info("pipeline_complete", records_read=len(records), records_written=count)
        return {"records_read": len(records), "records_written": count}
