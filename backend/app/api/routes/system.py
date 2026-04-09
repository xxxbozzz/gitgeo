"""System status endpoints."""

from fastapi import APIRouter

from backend.app.schemas.api import ApiResponse, ok_response
from backend.app.services.system_service import system_service


router = APIRouter(prefix="/system", tags=["system"])


@router.get("/status", response_model=ApiResponse)
def get_system_status() -> ApiResponse:
    """Return current backend and dependency status."""
    return ok_response(
        message="system_status_ready",
        data=system_service.get_status(),
    )
