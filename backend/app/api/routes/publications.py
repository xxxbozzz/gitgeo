"""Publication audit endpoints."""

from fastapi import APIRouter, Depends, Query

from backend.app.core.dependencies import get_publication_repo
from backend.app.repositories.publication import PublicationRepository
from backend.app.schemas.api import ApiResponse, fail_response, ok_response

router = APIRouter(prefix="/publications", tags=["publications"])


def _pub_item(p) -> dict:
    return {
        "id": p.id, "article_id": p.article_id, "platform": p.platform,
        "publish_mode": p.publish_mode, "status": p.status,
        "trigger_mode": p.trigger_mode, "attempt_no": p.attempt_no,
        "retry_of_publication_id": p.retry_of_publication_id,
        "external_id": p.external_id, "external_url": p.external_url,
        "message": p.message, "error_message": p.error_message,
        "created_at": p.created_at.isoformat() if p.created_at else None,
        "updated_at": p.updated_at.isoformat() if p.updated_at else None,
    }


@router.get("", response_model=ApiResponse)
async def list_publications(
    article_id: int | None = Query(default=None),
    platform: str | None = Query(default=None),
    status: str | None = Query(default=None),
    trigger_mode: str | None = Query(default=None),
    query: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    repo: PublicationRepository = Depends(get_publication_repo),
) -> ApiResponse:
    items, total = await repo.list_publications(
        article_id=article_id, platform=platform, status=status,
        trigger_mode=trigger_mode, query_text=query,
        limit=limit, offset=offset,
    )
    return ok_response(message="publications_list_ready", data={
        "items": [_pub_item(p) for p in items], "total": total,
        "limit": limit, "offset": offset,
    })


@router.get("/{publication_id}", response_model=ApiResponse)
async def get_publication_detail(
    publication_id: int,
    repo: PublicationRepository = Depends(get_publication_repo),
) -> ApiResponse:
    pub = await repo.get_by_id(publication_id)
    if not pub:
        return fail_response(message="publication_not_found", error_code="not_found")
    return ok_response(message="publication_detail_ready", data={
        "publication": {
            **_pub_item(pub),
            "request_payload_json": pub.request_payload_json,
            "response_payload_json": pub.response_payload_json,
        },
    })
