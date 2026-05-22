"""Capability center endpoints."""

from fastapi import APIRouter, Depends, Query

from backend.app.core.dependencies import get_capability_repo
from backend.app.repositories.capability import CapabilityRepository
from backend.app.schemas.api import ApiResponse, fail_response, ok_response

router = APIRouter(prefix="/capabilities", tags=["capabilities"])

# Default profile code — matches what capability_store uses
PROFILE_CODE = "shenya-pcb-v1"


@router.get("", response_model=ApiResponse)
async def list_capabilities(
    active: bool | None = Query(default=None),
    group_code: str | None = Query(default=None),
    query: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    repo: CapabilityRepository = Depends(get_capability_repo),
) -> ApiResponse:
    items, total = await repo.list_specs(
        profile_code=PROFILE_CODE, active=active,
        group_code=group_code, query_text=query,
        limit=limit, offset=offset,
    )
    active_total = await repo.active_count(profile_code=PROFILE_CODE)
    inactive_total = await repo.inactive_count(profile_code=PROFILE_CODE)
    groups_total = await repo.groups_count(profile_code=PROFILE_CODE)
    return ok_response(message="capabilities_list_ready", data={
        "items": items, "total": total, "limit": limit, "offset": offset,
        "active_total": active_total, "inactive_total": inactive_total,
        "groups_total": groups_total,
    })


@router.get("/{spec_id}", response_model=ApiResponse)
async def get_capability_detail(
    spec_id: int, repo: CapabilityRepository = Depends(get_capability_repo),
) -> ApiResponse:
    detail = await repo.get_spec_detail(profile_code=PROFILE_CODE, spec_id=spec_id)
    if not detail:
        return fail_response(message="capability_not_found", error_code="not_found")

    # Look up related articles
    terms = [str(detail.get("capability_name") or "").strip()]
    if detail.get("group_name"):
        terms.append(str(detail["group_name"]).strip())
    articles = []
    for term in terms:
        if not term:
            continue
        articles = await repo.find_articles_by_term(term)
        if articles:
            break

    return ok_response(message="capability_detail_ready", data={
        "capability": {**detail, "recent_articles": articles},
    })


@router.get("/{spec_id}/sources", response_model=ApiResponse)
async def list_capability_sources(
    spec_id: int, repo: CapabilityRepository = Depends(get_capability_repo),
) -> ApiResponse:
    items = await repo.list_spec_sources(profile_code=PROFILE_CODE, spec_id=spec_id)
    return ok_response(message="capability_sources_ready", data={
        "spec_id": spec_id, "items": items,
    })


@router.post("/{spec_id}/disable", response_model=ApiResponse)
async def disable_capability(
    spec_id: int, repo: CapabilityRepository = Depends(get_capability_repo),
) -> ApiResponse:
    rowcount = await repo.disable_spec(profile_code=PROFILE_CODE, spec_id=spec_id)
    if rowcount == 0:
        return ok_response(message="capability_already_disabled", data={
            "changed": False, "spec_id": spec_id,
        })
    return ok_response(message="capability_disabled", data={
        "changed": True, "spec_id": spec_id,
    })
