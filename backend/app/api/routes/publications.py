"""Publication audit endpoints."""

from fastapi import APIRouter, Query

from backend.app.schemas.api import ApiResponse, fail_response, ok_response
from backend.app.services.publications_service import publications_service


router = APIRouter(prefix="/publications", tags=["publications"])


@router.get("", response_model=ApiResponse)
def list_publications(
    article_id: int | None = Query(default=None, ge=1, description="Filter by article id"),
    channel: str | None = Query(default=None, description="Filter by channel"),
    platform: str | None = Query(default=None, description="Deprecated adapter/platform alias"),
    status: str | None = Query(default=None, description="Filter by publication status"),
    trigger_mode: str | None = Query(default=None, description="Filter by trigger mode"),
    query: str | None = Query(default=None, description="Title, slug, or external id fuzzy search"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> ApiResponse:
    """Return paginated publication audit records."""
    return ok_response(
        message="publications_list_ready",
        data=publications_service.list_publications(
            article_id=article_id,
            channel=channel,
            platform=platform,
            status=status,
            trigger_mode=trigger_mode,
            query_text=query,
            limit=limit,
            offset=offset,
        ),
    )


@router.get("/{publication_id}", response_model=ApiResponse)
def get_publication_detail(publication_id: int) -> ApiResponse:
    """Return a single publication audit record."""
    return ok_response(
        message="publication_detail_ready",
        data=publications_service.get_publication_detail(publication_id),
    )


@router.post("/{publication_id}/retry", response_model=ApiResponse)
def retry_publication(publication_id: int) -> ApiResponse:
    """Retry a failed or incomplete publication attempt."""
    result = publications_service.retry_publication(publication_id)
    if not result.get("success"):
        return fail_response(
            message=str(result.get("message") or "publication_retry_failed"),
            error_code=str(result.get("error_code") or "publication_retry_failed"),
            data=result,
        )
    return ok_response(message="publication_retry_completed", data=result)
