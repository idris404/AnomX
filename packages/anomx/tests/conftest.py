"""Shared pytest fixtures."""

from __future__ import annotations

import socket

import psycopg
import pytest

from tests.helpers import cleanup_stream as _cleanup_stream

DEFAULT_DSN = "postgresql://anomx:anomx@localhost:5433/anomx"


def postgres_available(dsn: str = DEFAULT_DSN) -> bool:
    try:
        host_port = dsn.rsplit("@", 1)[-1].rsplit("/", 1)[0]
        host, port_str = host_port.split(":")
        port = int(port_str)
        with socket.create_connection((host, port), timeout=1):
            pass
        with psycopg.connect(dsn) as connection:
            connection.execute("SELECT 1")
        return True
    except OSError:
        return False
    except psycopg.Error:
        return False


@pytest.fixture
def postgres_dsn() -> str:
    return DEFAULT_DSN


@pytest.fixture
def require_postgres(postgres_dsn: str) -> str:
    if not postgres_available(postgres_dsn):
        pytest.skip("PostgreSQL is not available on localhost:5433")
    return postgres_dsn


@pytest.fixture
def cleanup_stream(require_postgres: str):
    deleted: list[str] = []

    def _schedule(stream_name: str) -> None:
        deleted.append(stream_name)

    yield _schedule

    with psycopg.connect(require_postgres) as connection:
        for stream_name in deleted:
            _cleanup_stream(connection, stream_name)
