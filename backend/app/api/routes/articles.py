"""Article endpoints — async SQLAlchemy."""

from fastapi import APIRouter, Depends, Query

from backend.app.core.dependencies import get_article_repo
from backend.app.repositories.article import ArticleRepository
from backend.app.schemas.api import ApiResponse, fail_response, ok_response
from backend.app.schemas.articles import ArticlePublishRequest

router = APIRouter(prefix="/articles", tags=["articles"])


@router.get("", response_model=ApiResponse)
async def list_articles(
    status: str | None = Query(default=None, description="draft / approved / published"),
    min_score: int = Query(default=0, ge=0, le=100),
    query: str | None = Query(default=None, description="Title or slug fuzzy search"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    repo: ArticleRepository = Depends(get_article_repo),
) -> ApiResponse:
    articles, total = await repo.list_articles(
        status=status,
        min_score=min_score,
        query_text=query,
        limit=limit,
        offset=offset,
    )
    return ok_response(
        message="articles_list_ready",
        data={
            "items": [
                {
                    "id": a.id,
                    "title": a.title,
                    "slug": a.slug,
                    "publish_status": a.publish_status,
                    "quality_score": a.quality_score,
                    "created_at": a.created_at.isoformat() if a.created_at else None,
                    "updated_at": a.updated_at.isoformat() if a.updated_at else None,
                }
                for a in articles
            ],
            "total": total,
            "limit": limit,
            "offset": offset,
        },
    )


@router.get("/summary", response_model=ApiResponse)
async def get_articles_summary(
    repo: ArticleRepository = Depends(get_article_repo),
) -> ApiResponse:
    counts = await repo.status_counts()
    return ok_response(message="articles_summary_ready", data=counts)


@router.get("/{article_id}", response_model=ApiResponse)
async def get_article_detail(
    article_id: int,
    repo: ArticleRepository = Depends(get_article_repo),
) -> ApiResponse:
    article = await repo.get_by_id(article_id)
    if not article:
        return fail_response(message="article_not_found", error_code="not_found")
    return ok_response(
        message="article_detail_ready",
        data={
            "id": article.id,
            "title": article.title,
            "slug": article.slug,
            "content_markdown": article.content_markdown,
            "meta_json": article.meta_json,
            "quality_score": article.quality_score,
            "publish_status": article.publish_status,
            "dim_subject": article.dim_subject,
            "dim_action": article.dim_action,
            "dim_attribute": article.dim_attribute,
            "created_at": article.created_at.isoformat() if article.created_at else None,
            "updated_at": article.updated_at.isoformat() if article.updated_at else None,
        },
    )


@router.post("/{article_id}/refix", response_model=ApiResponse)
async def refix_article(article_id: int) -> ApiResponse:
    return fail_response(message="refix not yet available via async backend", error_code="not_implemented")


@router.post("/{article_id}/recycle", response_model=ApiResponse)
async def recycle_article(
    article_id: int,
    repo: ArticleRepository = Depends(get_article_repo),
) -> ApiResponse:
    article = await repo.get_by_id(article_id)
    if not article:
        return fail_response(message="article_not_found", error_code="not_found")
    await repo.delete(article_id)
    return ok_response(message="article_recycle_completed")


@router.post("/{article_id}/publish", response_model=ApiResponse)
async def publish_article(
    article_id: int,
    payload: ArticlePublishRequest,
    repo: ArticleRepository = Depends(get_article_repo),
) -> ApiResponse:
    article = await repo.get_by_id(article_id)
    if not article:
        return fail_response(message="article_not_found", error_code="not_found")
    # Publishing via adapters requires sync imports from core/ — delegate
    # For now, mark as approved if sufficient quality
    if article.quality_score is None or article.quality_score < 80:
        return fail_response(message="article_quality_insufficient_for_publish", error_code="quality_insufficient")
    await repo.update_status(article_id, 1)
    return ok_response(
        message="article_publish_completed",
        data={"article_id": article_id, "status": "approved"},
    )
