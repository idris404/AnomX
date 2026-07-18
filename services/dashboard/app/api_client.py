"""HTTP helpers for the Streamlit dashboard."""

from __future__ import annotations

import os
from typing import Any

import httpx

DEFAULT_API_URL = os.getenv("ANOMX_API_URL", "http://localhost:8000")


class ApiClient:
    """Thin wrapper around the AnomX REST API."""

    def __init__(self, base_url: str = DEFAULT_API_URL) -> None:
        self.base_url = base_url.rstrip("/")

    def get_json(self, path: str) -> dict[str, Any]:
        response = httpx.get(f"{self.base_url}{path}", timeout=10.0)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            msg = f"Unexpected API response for {path}"
            raise TypeError(msg)
        return payload

    def get_text(self, path: str) -> str:
        response = httpx.get(f"{self.base_url}{path}", timeout=10.0)
        response.raise_for_status()
        return response.text
