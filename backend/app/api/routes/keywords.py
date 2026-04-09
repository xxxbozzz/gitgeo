"""Keyword center endpoints."""

from fastapi import APIRouter, Query

from backend.app.schemas.api import ApiResponse, ok_response
from backend.app.services.keywords_service import keywords_service


router = APIRouter(tags=["keywords"])


@router.get("/keywords", response_model=ApiResponse)
def list_keywords(
    status: str | None = Query(default=None, description="pending / consumed"),
    query: str | None = Query(default=None, description="Keyword or article fuzzy search"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> ApiResponse:
    """Return paginated keyword pool records."""
    return ok_response(
        message="keywords_list_ready",
        data=keywords_service.list_keywords(
            status=status,
            query_text=query,
            limit=limit,
            offset=offset,
        ),
    )


@router.get("/gap-keywords", response_model=ApiResponse)
def list_gap_keywords(
    query: str | None = Query(default=None, description="Keyword fuzzy search"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> ApiResponse:
    """Return paginated pending/gap keywords."""
    return ok_response(
        message="gap_keywords_ready",
        data=keywords_service.list_gap_keywords(
            query_text=query,
            limit=limit,
            offset=offset,
        ),
    )


@router.get("/keywords/clusters", response_model=ApiResponse)
def list_keyword_clusters(limit: int = Query(default=12, ge=1, le=50)) -> ApiResponse:
    """Return keyword cluster distribution."""
    return ok_response(
        message="keyword_clusters_ready",
        data=keywords_service.list_clusters(limit=limit),
    )
