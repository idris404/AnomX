"""YAML configuration loading."""

from __future__ import annotations

from pathlib import Path
from typing import Any, TypeVar

import yaml
from pydantic import TypeAdapter

from anomx.benchmark.models import BenchmarkConfig
from anomx.config.detect_models import DetectConfig
from anomx.config.models import AppSettings, CsvBatchSourceConfig, SourceConfig

T = TypeVar("T")


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        msg = f"Expected mapping in config file: {path}"
        raise ValueError(msg)
    return data


def load_app_settings(path: Path | None = None) -> AppSettings:
    config_path = path or Path("config/settings.yaml")
    if not config_path.exists():
        return AppSettings()
    return AppSettings.model_validate(load_yaml(config_path))


def load_source_config(path: Path) -> SourceConfig:
    return TypeAdapter(SourceConfig).validate_python(load_yaml(path))


def load_csv_source_config(path: Path) -> CsvBatchSourceConfig:
    config = load_source_config(path)
    if not isinstance(config, CsvBatchSourceConfig):
        msg = f"Expected csv_batch source config: {path}"
        raise ValueError(msg)
    return config


def load_detect_config(path: Path) -> DetectConfig:
    return DetectConfig.model_validate(load_yaml(path))


def load_benchmark_config(path: Path) -> BenchmarkConfig:
    return BenchmarkConfig.model_validate(load_yaml(path))
