"""Health and readiness endpoints."""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from backend.app.core.settings import get_settings
from backend.app.db.mysql import database
from backend.app.schemas.api import ApiResponse, fail_response, ok_response
from core.build_info import format_build_label


router = APIRouter(tags=["health"])


@router.get("/health", response_model=ApiResponse)
def health_check() -> ApiResponse:
    """Basic liveness endpoint for process-level checks."""
    settings = get_settings()
    return ok_response(
        message="backend_alive",
        data={
            "service": settings.app_name,
            "version": settings.app_version,
            "environment": settings.app_env,
            "build": format_build_label(),
        },
    )


@router.get("/ready", response_model=ApiResponse)
def readiness_check():
    """Readiness endpoint that verifies database connectivity."""
    if database.ping():
        return ok_response(
            message="backend_ready",
            data={"database": "ok"},
        )

    return JSONResponse(
        status_code=503,
        content=fail_response(
            message="database_unavailable",
            error_code="DB_UNAVAILABLE",
            data={"database": "error"},
        ).model_dump(),
    )
