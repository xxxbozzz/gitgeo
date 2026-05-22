"""Job run repository."""

from __future__ import annotations

from typing import Optional

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models import JobRun, JobStep


class RunRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_runs(
        self, *, status: Optional[str] = None, trigger_mode: Optional[str] = None,
        keyword: Optional[str] = None, limit: int = 20, offset: int = 0,
    ) -> tuple[list[JobRun], int]:
        stmt = select(JobRun)
        if status:
            stmt = stmt.where(JobRun.status == status)
        if trigger_mode:
            stmt = stmt.where(JobRun.trigger_mode == trigger_mode)
        if keyword:
            stmt = stmt.where(JobRun.keyword.ilike(f"%{keyword.strip()}%"))

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.session.execute(count_stmt)).scalar() or 0

        stmt = stmt.order_by(JobRun.started_at.desc()).offset(offset).limit(limit)
        rows = (await self.session.execute(stmt)).scalars().all()
        return list(rows), total

    async def get_summary(self) -> dict:
        stmt = select(
            func.count().label("total_runs"),
            func.sum(case((JobRun.status == "running", 1), else_=0)).label("running_runs"),
            func.sum(case((JobRun.status == "succeeded", 1), else_=0)).label("succeeded_runs"),
            func.sum(case((JobRun.status == "failed", 1), else_=0)).label("failed_runs"),
            func.sum(case((JobRun.status == "partial", 1), else_=0)).label("partial_runs"),
            func.max(JobRun.started_at).label("latest_run_at"),
        )
        row = (await self.session.execute(stmt)).first()
        return {
            "total_runs": int(row.total_runs) if row.total_runs else 0,
            "running_runs": int(row.running_runs) if row.running_runs else 0,
            "succeeded_runs": int(row.succeeded_runs) if row.succeeded_runs else 0,
            "failed_runs": int(row.failed_runs) if row.failed_runs else 0,
            "partial_runs": int(row.partial_runs) if row.partial_runs else 0,
            "latest_run_at": row.latest_run_at.isoformat() if row.latest_run_at else None,
        }

    async def list_failures(self, *, limit: int = 20) -> list[JobRun]:
        stmt = select(JobRun).where(JobRun.status.in_(["failed", "partial"])).order_by(
            JobRun.started_at.desc()
        ).limit(limit)
        return list((await self.session.execute(stmt)).scalars().all())

    async def get_by_id(self, run_id: int) -> Optional[JobRun]:
        return await self.session.get(JobRun, run_id)

    async def list_steps(self, run_id: int) -> list[JobStep]:
        stmt = select(JobStep).where(JobStep.job_run_id == run_id).order_by(
            JobStep.started_at.asc(), JobStep.attempt_no.asc()
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def step_counts(self, run_id: int) -> dict:
        stmt = select(
            func.count().label("steps_total"),
            func.sum(case((JobStep.status == "failed", 1), else_=0)).label("failed_steps"),
        ).where(JobStep.job_run_id == run_id)
        row = (await self.session.execute(stmt)).first()
        return {
            "steps_total": int(row.steps_total) if row.steps_total else 0,
            "failed_steps": int(row.failed_steps) if row.failed_steps else 0,
        }
