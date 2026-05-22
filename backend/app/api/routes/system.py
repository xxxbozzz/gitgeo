"""System status endpoint."""

from fastapi import APIRouter, Depends

from backend.app.core.dependencies import get_system_repo
from backend.app.core.settings import get_settings
from backend.app.repositories.system import SystemRepository
from backend.app.schemas.api import ApiResponse, ok_response

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/status", response_model=ApiResponse)
async def system_status(repo: SystemRepository = Depends(get_system_repo)) -> ApiResponse:
    settings = get_settings()
    db_ok = await repo.ping()
    return ok_response(message="system_status_ready", data={
        "environment": settings.app_env,
        "debug": settings.app_debug,
        "database": "ok" if db_ok else "error",
        "llm_api_configured": repo.has_llm_credentials(),
        "version": settings.app_version,
    })
