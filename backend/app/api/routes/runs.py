"""Runtime run endpoints."""

from fastapi import APIRouter, Depends, Query

from backend.app.core.dependencies import get_run_repo
from backend.app.repositories.run import RunRepository
from backend.app.schemas.api import ApiResponse, ok_response

router = APIRouter(prefix="/runs", tags=["runs"])


def _run_item(r) -> dict:
    return {
        "id": r.id, "run_uid": r.run_uid, "run_type": r.run_type,
        "trigger_mode": r.trigger_mode, "keyword_id": r.keyword_id,
        "keyword": r.keyword, "article_id": r.article_id,
        "status": r.status, "current_step": r.current_step,
        "retry_count": r.retry_count, "error_message": r.error_message,
        "detail_json": r.detail_json,
        "started_at": r.started_at.isoformat() if r.started_at else None,
        "finished_at": r.finished_at.isoformat() if r.finished_at else None,
        "updated_at": r.updated_at.isoformat() if r.updated_at else None,
    }


def _step_item(s) -> dict:
    return {
        "id": s.id, "job_run_id": s.job_run_id, "step_code": s.step_code,
        "step_name": s.step_name, "attempt_no": s.attempt_no,
        "status": s.status, "article_id": s.article_id,
        "error_message": s.error_message, "detail_json": s.detail_json,
        "started_at": s.started_at.isoformat() if s.started_at else None,
        "finished_at": s.finished_at.isoformat() if s.finished_at else None,
        "updated_at": s.updated_at.isoformat() if s.updated_at else None,
    }


@router.get("", response_model=ApiResponse)
async def list_runs(
    status: str | None = Query(default=None),
    trigger_mode: str | None = Query(default=None),
    keyword: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    repo: RunRepository = Depends(get_run_repo),
) -> ApiResponse:
    items, total = await repo.list_runs(
        status=status, trigger_mode=trigger_mode, keyword=keyword,
        limit=limit, offset=offset,
    )
    return ok_response(message="runs_list_ready", data={
        "items": [_run_item(r) for r in items], "total": total, "limit": limit, "offset": offset,
    })


@router.get("/summary", response_model=ApiResponse)
async def get_summary(repo: RunRepository = Depends(get_run_repo)) -> ApiResponse:
    return ok_response(message="runs_summary_ready", data=await repo.get_summary())


@router.get("/failures", response_model=ApiResponse)
async def list_failures(
    limit: int = Query(default=20, ge=1, le=100),
    repo: RunRepository = Depends(get_run_repo),
) -> ApiResponse:
    items = await repo.list_failures(limit=limit)
    return ok_response(message="recent_failures_ready", data={
        "items": [_run_item(r) for r in items], "limit": limit,
    })


@router.get("/{run_id}", response_model=ApiResponse)
async def get_run_detail(run_id: int, repo: RunRepository = Depends(get_run_repo)) -> ApiResponse:
    run = await repo.get_by_id(run_id)
    counts = await repo.step_counts(run_id)
    return ok_response(message="run_detail_ready", data={
        "run": _run_item(run) if run else None,
        "steps_total": counts["steps_total"],
        "failed_steps": counts["failed_steps"],
    })


@router.get("/{run_id}/steps", response_model=ApiResponse)
async def list_run_steps(run_id: int, repo: RunRepository = Depends(get_run_repo)) -> ApiResponse:
    steps = await repo.list_steps(run_id)
    return ok_response(message="run_steps_ready", data={
        "run_id": run_id, "items": [_step_item(s) for s in steps],
    })
