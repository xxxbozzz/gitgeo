"""Overview endpoints."""

from fastapi import APIRouter, Query

from backend.app.schemas.api import ApiResponse, ok_response
from backend.app.services.overview_service import overview_service


router = APIRouter(prefix="/overview", tags=["overview"])


@router.get("/kpis", response_model=ApiResponse)
def get_overview_kpis() -> ApiResponse:
    """Return top-level dashboard KPIs."""
    return ok_response(
        message="overview_kpis_ready",
        data=overview_service.get_kpis(),
    )


@router.get("/trend", response_model=ApiResponse)
def get_overview_trend(days: int = Query(default=7, ge=1, le=30)) -> ApiResponse:
    """Return article production trend for the last N days."""
    return ok_response(
        message="overview_trend_ready",
        data=overview_service.get_trend(days=days),
    )


@router.get("/board", response_model=ApiResponse)
def get_overview_board(
    pending_limit: int = Query(default=5, ge=1, le=20),
    article_limit: int = Query(default=5, ge=1, le=20),
) -> ApiResponse:
    """Return overview board columns."""
    return ok_response(
        message="overview_board_ready",
        data=overview_service.get_board(
            pending_limit=pending_limit,
            article_limit=article_limit,
        ),
    )


@router.get("/latest-articles", response_model=ApiResponse)
def get_latest_articles(limit: int = Query(default=8, ge=1, le=30)) -> ApiResponse:
    """Return latest article cards for the overview page."""
    return ok_response(
        message="overview_latest_articles_ready",
        data=overview_service.get_latest_articles(limit=limit),
    )
