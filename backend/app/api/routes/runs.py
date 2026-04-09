"""Runtime job endpoints."""

from fastapi import APIRouter, Query

from backend.app.schemas.api import ApiResponse, ok_response
from backend.app.services.runs_service import runs_service


router = APIRouter(prefix="/runs", tags=["runs"])


@router.get("", response_model=ApiResponse)
def list_runs(
    status: str | None = Query(default=None, description="Filter by run status"),
    trigger_mode: str | None = Query(default=None, description="Filter by trigger mode"),
    keyword: str | None = Query(default=None, description="Keyword fuzzy search"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> ApiResponse:
    """Return paginated run records."""
    return ok_response(
        message="runs_list_ready",
        data=runs_service.list_runs(
            status=status,
            trigger_mode=trigger_mode,
            keyword=keyword,
            limit=limit,
            offset=offset,
        ),
    )


@router.get("/summary", response_model=ApiResponse)
def get_runs_summary() -> ApiResponse:
    """Return run status summary for dashboard widgets."""
    return ok_response(
        message="runs_summary_ready",
        data=runs_service.get_summary(),
    )


@router.get("/recent-failures", response_model=ApiResponse)
def get_recent_failures(limit: int = Query(default=10, ge=1, le=50)) -> ApiResponse:
    """Return recent failed or partial runs."""
    return ok_response(
        message="runs_recent_failures_ready",
        data=runs_service.list_recent_failures(limit=limit),
    )


@router.get("/{run_id}", response_model=ApiResponse)
def get_run_detail(run_id: int) -> ApiResponse:
    """Return a single run detail."""
    return ok_response(
        message="run_detail_ready",
        data=runs_service.get_run_detail(run_id),
    )


@router.get("/{run_id}/steps", response_model=ApiResponse)
def get_run_steps(run_id: int) -> ApiResponse:
    """Return timeline steps for a single run."""
    return ok_response(
        message="run_steps_ready",
        data=runs_service.list_run_steps(run_id),
    )
