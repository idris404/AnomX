"""NAB (Numenta Anomaly Benchmark) batch source connector."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import structlog

from anomx.connectors.common import load_timeseries_frame, records_from_timeseries_frame

logger = structlog.get_logger(__name__)


class NabBatchSource:
    """Reads a NAB CSV time series and optionally attaches point labels from NAB windows."""

    def __init__(
        self,
        path: Path,
        dataset_name: str,
        *,
        timestamp_column: str = "timestamp",
        value_column: str = "value",
        labels_path: Path | None = None,
        labels_key: str | None = None,
    ) -> None:
        self._path = path
        self._dataset_name = dataset_name
        self._timestamp_column = timestamp_column
        self._value_column = value_column
        self._labels_path = labels_path
        self._labels_key = labels_key or dataset_name

    def read(self) -> list[dict[str, Any]]:
        frame = load_timeseries_frame(
            self._path,
            timestamp_column=self._timestamp_column,
            value_column=self._value_column,
        )
        windows = _load_anomaly_windows(self._labels_path, self._labels_key)

        records = records_from_timeseries_frame(
            frame,
            timestamp_column=self._timestamp_column,
            value_column=self._value_column,
            extra_payload={"dataset": self._dataset_name},
            row_extra=lambda _row, observed_at: {
                "label": int(_timestamp_in_windows(observed_at, windows)),
            },
        )

        logger.info(
            "nab_batch_read_complete",
            path=str(self._path),
            dataset=self._dataset_name,
            rows=len(records),
            labeled_points=sum(record["payload"].get("label", 0) for record in records),
        )
        return records


def _load_anomaly_windows(labels_path: Path | None, labels_key: str) -> list[tuple[datetime, datetime]]:
    if labels_path is None or not labels_path.exists():
        return []

    raw = json.loads(labels_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return []

    candidates = [
        labels_key,
        f"realKnownCause/{labels_key}.csv",
        f"realKnownCause/{labels_key}",
    ]
    windows_raw = None
    for candidate in candidates:
        if candidate in raw:
            windows_raw = raw[candidate]
            break
    if windows_raw is None:
        return []

    windows: list[tuple[datetime, datetime]] = []
    for window in windows_raw:
        if not isinstance(window, list) or len(window) != 2:
            continue
        start = _parse_window_timestamp(str(window[0]))
        end = _parse_window_timestamp(str(window[1]))
        windows.append((start, end))
    return windows


def _parse_window_timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace(" ", "T"))
    if parsed.tzinfo is None:
        from datetime import UTC

        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _timestamp_in_windows(observed_at: datetime, windows: list[tuple[datetime, datetime]]) -> bool:
    for start, end in windows:
        if start <= observed_at <= end:
            return True
    return False
