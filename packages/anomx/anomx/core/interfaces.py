"""Core protocol interfaces for the AnomX pipeline."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

import structlog

logger = structlog.get_logger(__name__)


@runtime_checkable
class Source(Protocol):
    """Reads raw observations from an external data source."""

    def read(self) -> list[dict[str, Any]]:
        """Return a batch of raw observation records."""
        ...


@runtime_checkable
class Sink(Protocol):
    """Persists processed records to a storage backend."""

    def write(self, records: list[dict[str, Any]]) -> int:
        """Write records and return the number persisted."""
        ...


@runtime_checkable
class Detector(Protocol):
    """Scores observations and flags anomalies."""

    def fit(self, data: list[dict[str, Any]]) -> None:
        """Fit the detector on a reference window."""
        ...

    def score(self, data: list[dict[str, Any]]) -> list[float]:
        """Return an anomaly score per observation (higher = more anomalous)."""
        ...

    def predict(self, data: list[dict[str, Any]]) -> list[bool]:
        """Return a boolean anomaly flag per observation."""
        ...


@runtime_checkable
class Alerter(Protocol):
    """Dispatches alerts when anomalies are detected."""

    def send(self, alert: dict[str, Any]) -> None:
        """Send a single alert payload."""
        ...
