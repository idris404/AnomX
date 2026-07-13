"""Detection configuration models."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class CalibrationConfig(BaseModel):
    method: Literal["percentile"] = "percentile"
    percentile: float = Field(default=95.0, gt=0.0, lt=100.0)


class DetectorConfig(BaseModel):
    name: str = Field(min_length=1)
    type: Literal["mad", "isolation_forest"]
    weight: float = Field(default=1.0, gt=0.0)
    params: dict[str, Any] = Field(default_factory=dict)


class DetectDefaults(BaseModel):
    calibration: CalibrationConfig = Field(default_factory=CalibrationConfig)
    fit_ratio: float = Field(default=0.8, gt=0.0, lt=1.0)
    value_key: str = "value"


class DetectConfig(BaseModel):
    defaults: DetectDefaults = Field(default_factory=DetectDefaults)
    detectors: list[DetectorConfig] = Field(min_length=1)
