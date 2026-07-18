"""Path helpers — resolve config paths from the AnomX repo root."""

import os
from pathlib import Path

_REPO_ROOT: Path | None = None


def _find_repo_root() -> Path:
    env_root = os.environ.get("ANOMX_REPO_ROOT")
    if env_root:
        root = Path(env_root).resolve()
        if (root / "config" / "settings.yaml").is_file():
            return root
        msg = f"ANOMX_REPO_ROOT does not contain config/settings.yaml: {root}"
        raise FileNotFoundError(msg)

    candidate = Path(__file__).resolve().parent
    for _ in range(8):
        if (candidate / "config" / "settings.yaml").is_file() and (
            candidate / "packages" / "anomx"
        ).is_dir():
            return candidate
        candidate = candidate.parent

    msg = "Could not locate AnomX repo root (expected config/settings.yaml)"
    raise FileNotFoundError(msg)


def repo_root() -> Path:
    global _REPO_ROOT
    if _REPO_ROOT is None:
        _REPO_ROOT = _find_repo_root()
    return _REPO_ROOT


def repo_path(relative: str) -> Path:
    return repo_root() / relative
