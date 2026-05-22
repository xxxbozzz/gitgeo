"""Overview / Dashboard endpoints."""

from fastapi import APIRouter, Depends, Query

from backend.app.core.dependencies import get_keyword_repo, get_overview_repo
from backend.app.repositories.keyword import KeywordRepository
from backend.app.repositories.overview import OverviewRepository
from backend.app.schemas.api import ApiResponse, ok_response

router = APIRouter(prefix="/overview", tags=["overview"])


def _article_item(a) -> dict:
    return {
        "id": a.id, "title": a.title, "slug": a.slug,
        "quality_score": a.quality_score or 0, "publish_status": a.publish_status or 0,
        "dim_subject": a.dim_subject, "dim_action": a.dim_action,
        "dim_attribute": a.dim_attribute,
        "created_at": a.created_at.isoformat() if a.created_at else None,
        "updated_at": a.updated_at.isoformat() if a.updated_at else None,
    }


@router.get("/kpis", response_model=ApiResponse)
async def get_kpis(repo: OverviewRepository = Depends(get_overview_repo)) -> ApiResponse:
    return ok_response(message="overview_kpis_ready", data=await repo.get_kpis())


@router.get("/trend", response_model=ApiResponse)
async def get_trend(
    days: int = Query(default=30, ge=1, le=365),
    repo: OverviewRepository = Depends(get_overview_repo),
) -> ApiResponse:
    items = await repo.get_trend(days=days)
    return ok_response(message="overview_trend_ready", data={"days": days, "items": items})


@router.get("/board", response_model=ApiResponse)
async def get_board(
    pending_limit: int = Query(default=20, ge=1, le=100),
    article_limit: int = Query(default=20, ge=1, le=100),
    overview_repo: OverviewRepository = Depends(get_overview_repo),
    kw_repo: KeywordRepository = Depends(get_keyword_repo),
) -> ApiResponse:
    pending_kw = await kw_repo.list_pending(limit=pending_limit)
    drafts = await overview_repo.list_drafts(limit=article_limit)
    ready = await overview_repo.list_ready(limit=article_limit)
    return ok_response(message="overview_board_ready", data={
        "pending_keywords": pending_kw,
        "draft_articles": [_article_item(a) for a in drafts],
        "ready_articles": [_article_item(a) for a in ready],
    })


@router.get("/latest-articles", response_model=ApiResponse)
async def get_latest_articles(
    limit: int = Query(default=20, ge=1, le=100),
    repo: OverviewRepository = Depends(get_overview_repo),
) -> ApiResponse:
    articles = await repo.list_latest_articles(limit=limit)
    return ok_response(message="latest_articles_ready", data={
        "items": [_article_item(a) for a in articles], "limit": limit,
    })
