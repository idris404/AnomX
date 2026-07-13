"""Explanation payload models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class DetectorExplanation(BaseModel):
    """Per-detector human-readable explanation."""

    detector: str
    summary: str
    rules: list[str] = Field(default_factory=list)
    contributions: dict[str, float] = Field(default_factory=dict)
    details: dict[str, Any] = Field(default_factory=dict)


class Explanation(BaseModel):
    """Full explanation stored in alerts.explanation JSONB."""

    summary: str
    primary_detector: str
    ensemble_score: float
    ensemble_threshold: float
    observed_at: str
    value: float | None = None
    detector_scores: dict[str, float] = Field(default_factory=dict)
    feature_contributions: dict[str, float] = Field(default_factory=dict)
    rules: list[str] = Field(default_factory=list)
    detectors: list[DetectorExplanation] = Field(default_factory=list)

    def to_storage_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")
