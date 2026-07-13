"""Storage layer protocol interfaces."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Repository(Protocol):
    """Generic persistence interface for domain entities."""

    def save(self, entity: dict[str, Any]) -> str:
        """Persist an entity and return its identifier."""
        ...

    def get(self, entity_id: str) -> dict[str, Any] | None:
        """Retrieve an entity by identifier."""
        ...
