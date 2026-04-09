"""Article read endpoints."""

from fastapi import APIRouter, Query

from backend.app.schemas.api import ApiResponse, fail_response, ok_response
from backend.app.schemas.articles import ArticlePublishRequest
from backend.app.services.articles_service import articles_service


router = APIRouter(prefix="/articles", tags=["articles"])


@router.get("", response_model=ApiResponse)
def list_articles(
    status: str | None = Query(default=None, description="draft / approved / published"),
    min_score: int = Query(default=0, ge=0, le=100),
    query: str | None = Query(default=None, description="Title or slug fuzzy search"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> ApiResponse:
    """Return paginated article list."""
    return ok_response(
        message="articles_list_ready",
        data=articles_service.list_articles(
            status=status,
            min_score=min_score,
            query_text=query,
            limit=limit,
            offset=offset,
        ),
    )


@router.get("/summary", response_model=ApiResponse)
def get_articles_summary() -> ApiResponse:
    """Return aggregate article status counts."""
    return ok_response(
        message="articles_summary_ready",
        data=articles_service.get_summary(),
    )


@router.get("/{article_id}", response_model=ApiResponse)
def get_article_detail(article_id: int) -> ApiResponse:
    """Return single article detail."""
    return ok_response(
        message="article_detail_ready",
        data=articles_service.get_article_detail(article_id),
    )


@router.post("/{article_id}/refix", response_model=ApiResponse)
def refix_article(article_id: int) -> ApiResponse:
    """Run backend-managed article refix flow."""
    result = articles_service.refix_article(article_id)
    if not result.get("success"):
        return fail_response(
            message=str(result.get("message") or "article_refix_failed"),
            error_code=str(result.get("error_code") or "article_refix_failed"),
            data=result,
        )
    return ok_response(message="article_refix_completed", data=result)


@router.post("/{article_id}/recycle", response_model=ApiResponse)
def recycle_article(article_id: int) -> ApiResponse:
    """Recycle keyword bindings and delete the article."""
    result = articles_service.recycle_article(article_id)
    if not result.get("success"):
        return fail_response(
            message=str(result.get("message") or "article_recycle_failed"),
            error_code=str(result.get("error_code") or "article_recycle_failed"),
            data=result,
        )
    return ok_response(message="article_recycle_completed", data=result)


@router.post("/{article_id}/publish", response_model=ApiResponse)
def publish_article(article_id: int, payload: ArticlePublishRequest) -> ApiResponse:
    """Publish an article to one or more channels via channel adapters."""
    result = articles_service.publish_article(
        article_id,
        channels=payload.channels,
        go_live=payload.go_live,
    )
    if not result.get("success"):
        return fail_response(
            message=str(result.get("message") or "article_publish_failed"),
            error_code=str(result.get("error_code") or "article_publish_failed"),
            data=result,
        )
    return ok_response(message="article_publish_completed", data=result)
