"""Capability center endpoints."""

from fastapi import APIRouter, Query

from backend.app.schemas.api import ApiResponse, fail_response, ok_response
from backend.app.services.capabilities_service import capabilities_service


router = APIRouter(prefix="/capabilities", tags=["capabilities"])


@router.get("", response_model=ApiResponse)
def list_capabilities(
    active: bool | None = Query(default=None, description="Filter by active status"),
    group_code: str | None = Query(default=None, description="Filter by group code"),
    query: str | None = Query(default=None, description="Capability fuzzy search"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> ApiResponse:
    """Return paginated capability list."""
    return ok_response(
        message="capabilities_list_ready",
        data=capabilities_service.list_capabilities(
            active=active,
            group_code=group_code,
            query_text=query,
            limit=limit,
            offset=offset,
        ),
    )


@router.get("/{spec_id}", response_model=ApiResponse)
def get_capability_detail(spec_id: int) -> ApiResponse:
    """Return capability detail."""
    return ok_response(
        message="capability_detail_ready",
        data=capabilities_service.get_capability_detail(spec_id),
    )


@router.get("/{spec_id}/sources", response_model=ApiResponse)
def get_capability_sources(spec_id: int) -> ApiResponse:
    """Return capability sources."""
    return ok_response(
        message="capability_sources_ready",
        data=capabilities_service.list_capability_sources(spec_id),
    )


@router.post("/{spec_id}/disable", response_model=ApiResponse)
def disable_capability(spec_id: int) -> ApiResponse:
    """Disable a capability item."""
    result = capabilities_service.disable_capability(spec_id)
    if not result.get("success"):
        return fail_response(
            message=str(result.get("message") or "capability_disable_failed"),
            error_code=str(result.get("error_code") or "capability_disable_failed"),
            data=result,
        )
    return ok_response(message="capability_disable_completed", data=result)
