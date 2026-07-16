"""CSV/Parquet batch source connector."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import structlog

from anomx.connectors.common import load_timeseries_frame, records_from_timeseries_frame

logger = structlog.get_logger(__name__)


class CsvBatchSource:
    """Reads and validates a local CSV or Parquet file via Polars."""

    def __init__(
        self,
        path: Path,
        timestamp_column: str,
        value_column: str,
        *,
        file_format: Literal["csv", "parquet"] = "csv",
        include_columns: list[str] | None = None,
    ) -> None:
        self._path = path
        self._timestamp_column = timestamp_column
        self._value_column = value_column
        self._file_format = file_format
        self._include_columns = include_columns

    def read(self) -> list[dict[str, Any]]:
        frame = load_timeseries_frame(
            self._path,
            timestamp_column=self._timestamp_column,
            value_column=self._value_column,
            file_format=self._file_format,
        )
        records = records_from_timeseries_frame(
            frame,
            timestamp_column=self._timestamp_column,
            value_column=self._value_column,
            include_columns=self._include_columns,
        )

        logger.info(
            "csv_batch_read_complete",
            path=str(self._path),
            rows=len(records),
        )
        return records
