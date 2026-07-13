"""PostgreSQL connection helpers."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

import psycopg
from psycopg.rows import dict_row


@contextmanager
def postgres_connection(dsn: str) -> Iterator[psycopg.Connection[Any]]:
    connection = psycopg.connect(dsn, row_factory=dict_row)
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
