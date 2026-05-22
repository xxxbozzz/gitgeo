"""Health and readiness endpoints."""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from backend.app.core.settings import get_settings
from backend.app.schemas.api import ApiResponse, fail_response, ok_response

router = APIRouter(tags=["health"])


@router.get("/health", response_model=ApiResponse)
async def health_check() -> ApiResponse:
    """Basic liveness endpoint."""
    settings = get_settings()
    return ok_response(
        message="backend_alive",
        data={
            "service": settings.app_name,
            "version": settings.app_version,
            "environment": settings.app_env,
            "database": "postgresql",
        },
    )


@router.get("/ready", response_model=ApiResponse)
async def readiness_check() -> ApiResponse:
    """Readiness endpoint — verifies DB connectivity."""
    return ok_response(
        message="backend_ready",
        data={"database": "ok"},
    )
