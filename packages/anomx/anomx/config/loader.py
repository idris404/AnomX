"""YAML configuration loading."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from anomx.config.models import AppSettings, CsvBatchSourceConfig


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


def load_csv_source_config(path: Path) -> CsvBatchSourceConfig:
    return CsvBatchSourceConfig.model_validate(load_yaml(path))
