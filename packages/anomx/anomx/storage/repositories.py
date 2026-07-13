"""In-memory repository stub for Phase 0 testing."""

from __future__ import annotations

from typing import Any
from uuid import uuid4


class InMemoryRepository:
    """Simple dict-backed repository for unit tests and local dev."""

    def __init__(self) -> None:
        self._store: dict[str, dict[str, Any]] = {}

    def save(self, entity: dict[str, Any]) -> str:
        entity_id = str(entity.get("id", uuid4()))
        self._store[entity_id] = {**entity, "id": entity_id}
        return entity_id

    def get(self, entity_id: str) -> dict[str, Any] | None:
        return self._store.get(entity_id)
