"""Lightweight backend API client for the Streamlit dashboard."""

from __future__ import annotations

import os
from typing import Any

import requests


DEFAULT_TIMEOUT_SECONDS = float(os.getenv("GEO_BACKEND_API_TIMEOUT", "4"))
DEFAULT_ACTION_TIMEOUT_SECONDS = float(os.getenv("GEO_BACKEND_ACTION_TIMEOUT", "120"))


def get_backend_api_base() -> str:
    """Return the configured backend API base URL."""
    return os.getenv("GEO_BACKEND_API_BASE_URL", "http://localhost:8001/api/v1").rstrip("/")

def request_backend_data(
    method: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    json: dict[str, Any] | None = None,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> tuple[Any | None, str | None]:
    """Fetch a backend payload and return `(data, error)`."""
    url = f"{get_backend_api_base()}/{path.lstrip('/')}"
    try:
        response = requests.request(
            method=method.upper(),
            url=url,
            params=params,
            json=json,
            timeout=timeout,
        )
        response.raise_for_status()
        payload = response.json()
        if not payload.get("success", False):
            message = payload.get("message") or payload.get("error_code") or "backend_request_failed"
            return payload.get("data"), str(message)
        return payload.get("data"), None
    except Exception as exc:
        return None, str(exc)


def fetch_backend_data(
    path: str,
    *,
    params: dict[str, Any] | None = None,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> tuple[Any | None, str | None]:
    """Convenience GET wrapper."""
    return request_backend_data("GET", path, params=params, timeout=timeout)


def post_backend_data(
    path: str,
    *,
    json: dict[str, Any] | None = None,
    timeout: float = DEFAULT_ACTION_TIMEOUT_SECONDS,
) -> tuple[Any | None, str | None]:
    """Convenience POST wrapper for slower write operations."""
    return request_backend_data("POST", path, json=json, timeout=timeout)
