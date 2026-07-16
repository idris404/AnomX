"""PostgreSQL query batch source connector."""

from __future__ import annotations

from typing import Any

import structlog

from anomx.connectors.common import coerce_timestamp
from anomx.config.models import DatabaseSettings
from anomx.storage.postgres import postgres_connection

logger = structlog.get_logger(__name__)


class PostgresQuerySource:
    """Runs a SQL snapshot query and maps rows to observation records."""

    def __init__(
        self,
        database: DatabaseSettings,
        query: str,
        *,
        timestamp_column: str,
        value_column: str,
    ) -> None:
        self._database = database
        self._query = query.strip()
        self._timestamp_column = timestamp_column
        self._value_column = value_column

    def read(self) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        with postgres_connection(self._database.dsn) as connection:
            rows = connection.execute(self._query).fetchall()

        for row in rows:
            mapping = row
            if self._timestamp_column not in mapping:
                msg = f"Missing timestamp column in query result: {self._timestamp_column}"
                raise ValueError(msg)
            if self._value_column not in mapping:
                msg = f"Missing value column in query result: {self._value_column}"
                raise ValueError(msg)

            observed_at = coerce_timestamp(mapping[self._timestamp_column])
            value = float(mapping[self._value_column])
            payload = {
                key: _json_safe(value_item)
                for key, value_item in mapping.items()
                if key not in {self._timestamp_column, self._value_column}
            }
            payload[self._value_column] = value
            records.append({"observed_at": observed_at, "payload": payload})

        logger.info("postgres_query_read_complete", rows=len(records))
        return records


def _json_safe(value: Any) -> Any:
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value
