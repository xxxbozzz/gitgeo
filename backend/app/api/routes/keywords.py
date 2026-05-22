"""Keyword endpoints."""

from fastapi import APIRouter, Depends, Query

from backend.app.core.dependencies import get_keyword_repo
from backend.app.repositories.keyword import KeywordRepository
from backend.app.schemas.api import ApiResponse, ok_response

router = APIRouter(prefix="/keywords", tags=["keywords"])


@router.get("", response_model=ApiResponse)
async def list_keywords(
    status: str | None = Query(default=None),
    query: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    repo: KeywordRepository = Depends(get_keyword_repo),
) -> ApiResponse:
    items, total = await repo.list_keywords(status=status, query_text=query, limit=limit, offset=offset)
    return ok_response(message="keywords_list_ready", data={
        "items": items, "total": total, "limit": limit, "offset": offset,
    })


@router.get("/gap", response_model=ApiResponse)
async def list_gap_keywords(
    query: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    repo: KeywordRepository = Depends(get_keyword_repo),
) -> ApiResponse:
    items, total = await repo.list_keywords(status="pending", query_text=query, limit=limit, offset=offset)
    return ok_response(message="gap_keywords_ready", data={
        "items": items, "total": total, "limit": limit, "offset": offset,
    })


@router.get("/clusters", response_model=ApiResponse)
async def list_clusters(
    limit: int = Query(default=50, ge=1, le=200),
    repo: KeywordRepository = Depends(get_keyword_repo),
) -> ApiResponse:
    items = await repo.list_clusters(limit=limit)
    return ok_response(message="keyword_clusters_ready", data={"items": items, "limit": limit})
