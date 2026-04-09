"""Shared API response envelope."""

from typing import Any

from pydantic import BaseModel


class ApiResponse(BaseModel):
    """Standard API response format."""

    success: bool
    message: str
    data: Any | None = None
    error_code: str | None = None


def ok_response(message: str = "ok", data: Any | None = None) -> ApiResponse:
    """Return a success response envelope."""
    return ApiResponse(success=True, message=message, data=data, error_code=None)


def fail_response(
    message: str,
    error_code: str,
    data: Any | None = None,
) -> ApiResponse:
    """Return a failure response envelope."""
    return ApiResponse(success=False, message=message, data=data, error_code=error_code)
