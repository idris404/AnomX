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


def load_source_config(path: Path, *, path_base: Path | None = None) -> SourceConfig:
    data = load_yaml(path)
    if path_base is not None:
        data = _resolve_relative_source_paths(data, path_base)
    return TypeAdapter(SourceConfig).validate_python(data)


def _resolve_relative_source_paths(data: dict[str, Any], base: Path) -> dict[str, Any]:
    """Resolve relative file paths in source YAML against a project root."""
    resolved = dict(data)
    for key in ("path", "labels_path"):
        value = resolved.get(key)
        if isinstance(value, str):
            candidate = Path(value)
            if not candidate.is_absolute():
                resolved[key] = str((base / candidate).resolve())
    return resolved


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
