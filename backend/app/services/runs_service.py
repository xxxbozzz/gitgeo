"""Runtime run service."""

from __future__ import annotations

import json
from typing import Any

from backend.app.db.mysql import database
from backend.app.schemas.runs import (
    RunDetailPayload,
    RunFailuresPayload,
    RunListPayload,
    RunStepItem,
    RunStepsPayload,
    RunSummaryItem,
    RunSummaryPayload,
)


def _decode_detail(value: Any) -> dict[str, Any] | list[Any] | None:
    if value in (None, "", b""):
        return None
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="ignore")
    if isinstance(value, str):
        try:
            loaded = json.loads(value)
            if isinstance(loaded, (dict, list)):
                return loaded
        except Exception:
            return None
    return None


def _map_run(row: dict[str, Any]) -> RunSummaryItem:
    return RunSummaryItem(
        id=int(row["id"]),
        run_uid=str(row["run_uid"]),
        run_type=str(row["run_type"]),
        trigger_mode=str(row["trigger_mode"]),
        keyword_id=row.get("keyword_id"),
        keyword=str(row["keyword"]),
        article_id=row.get("article_id"),
        status=str(row["status"]),
        current_step=row.get("current_step"),
        retry_count=int(row.get("retry_count") or 0),
        error_message=row.get("error_message"),
        detail_json=_decode_detail(row.get("detail_json")),
        started_at=row.get("started_at"),
        finished_at=row.get("finished_at"),
        updated_at=row.get("updated_at"),
    )


def _map_step(row: dict[str, Any]) -> RunStepItem:
    return RunStepItem(
        id=int(row["id"]),
        job_run_id=int(row["job_run_id"]),
        step_code=str(row["step_code"]),
        step_name=str(row["step_name"]),
        attempt_no=int(row.get("attempt_no") or 1),
        status=str(row["status"]),
        article_id=row.get("article_id"),
        error_message=row.get("error_message"),
        detail_json=_decode_detail(row.get("detail_json")),
        started_at=row.get("started_at"),
        finished_at=row.get("finished_at"),
        updated_at=row.get("updated_at"),
    )


class RunsService:
    """Read-only runtime query service."""

    base_run_sql = """
        SELECT
            id, run_uid, run_type, trigger_mode, keyword_id, keyword, article_id,
            status, current_step, retry_count, error_message, detail_json,
            started_at, finished_at, updated_at
        FROM geo_job_runs
    """

    def _build_run_filters(
        self,
        *,
        status: str | None,
        trigger_mode: str | None,
        keyword: str | None,
    ) -> tuple[str, tuple[Any, ...]]:
        clauses: list[str] = []
        params: list[Any] = []

        if status:
            clauses.append("status = %s")
            params.append(status)
        if trigger_mode:
            clauses.append("trigger_mode = %s")
            params.append(trigger_mode)
        if keyword:
            clauses.append("keyword LIKE %s")
            params.append(f"%{keyword.strip()}%")

        where_sql = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        return where_sql, tuple(params)

    def list_runs(
        self,
        *,
        status: str | None,
        trigger_mode: str | None,
        keyword: str | None,
        limit: int,
        offset: int,
    ) -> RunListPayload:
        try:
            where_sql, params = self._build_run_filters(
                status=status,
                trigger_mode=trigger_mode,
                keyword=keyword,
            )
            total = int(
                database.fetch_value(
                    f"SELECT COUNT(*) AS value FROM geo_job_runs{where_sql}",
                    params=params,
                    default=0,
                )
                or 0
            )
            rows = database.fetch_all(
                f"{self.base_run_sql}{where_sql} ORDER BY started_at DESC LIMIT %s OFFSET %s",
                params=(*params, limit, offset),
            )
            return RunListPayload(
                items=[_map_run(row) for row in rows],
                total=total,
                limit=limit,
                offset=offset,
                warning=None,
            )
        except Exception as exc:
            return RunListPayload(
                items=[],
                total=0,
                limit=limit,
                offset=offset,
                warning=f"runs_unavailable: {exc}",
            )

    def get_summary(self) -> RunSummaryPayload:
        try:
            row = database.fetch_one(
                """
                SELECT
                    COUNT(*) AS total_runs,
                    SUM(CASE WHEN status = 'running' THEN 1 ELSE 0 END) AS running_runs,
                    SUM(CASE WHEN status = 'succeeded' THEN 1 ELSE 0 END) AS succeeded_runs,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed_runs,
                    SUM(CASE WHEN status = 'partial' THEN 1 ELSE 0 END) AS partial_runs,
                    MAX(started_at) AS latest_run_at
                FROM geo_job_runs
                """
            ) or {}
            return RunSummaryPayload(
                total_runs=int(row.get("total_runs") or 0),
                running_runs=int(row.get("running_runs") or 0),
                succeeded_runs=int(row.get("succeeded_runs") or 0),
                failed_runs=int(row.get("failed_runs") or 0),
                partial_runs=int(row.get("partial_runs") or 0),
                latest_run_at=row.get("latest_run_at"),
                warning=None,
            )
        except Exception as exc:
            return RunSummaryPayload(
                total_runs=0,
                running_runs=0,
                succeeded_runs=0,
                failed_runs=0,
                partial_runs=0,
                latest_run_at=None,
                warning=f"runs_summary_unavailable: {exc}",
            )

    def list_recent_failures(self, *, limit: int) -> RunFailuresPayload:
        try:
            rows = database.fetch_all(
                f"""
                {self.base_run_sql}
                WHERE status IN ('failed', 'partial')
                ORDER BY started_at DESC
                LIMIT %s
                """,
                params=(limit,),
            )
            return RunFailuresPayload(
                items=[_map_run(row) for row in rows],
                limit=limit,
                warning=None,
            )
        except Exception as exc:
            return RunFailuresPayload(
                items=[],
                limit=limit,
                warning=f"recent_failures_unavailable: {exc}",
            )

    def get_run_detail(self, run_id: int) -> RunDetailPayload:
        try:
            row = database.fetch_one(
                f"{self.base_run_sql} WHERE id = %s",
                params=(run_id,),
            )
            counts = database.fetch_one(
                """
                SELECT
                    COUNT(*) AS steps_total,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed_steps
                FROM geo_job_steps
                WHERE job_run_id = %s
                """,
                params=(run_id,),
            ) or {}
            return RunDetailPayload(
                run=_map_run(row) if row else None,
                steps_total=int(counts.get("steps_total") or 0),
                failed_steps=int(counts.get("failed_steps") or 0),
                warning=None,
            )
        except Exception as exc:
            return RunDetailPayload(
                run=None,
                steps_total=0,
                failed_steps=0,
                warning=f"run_detail_unavailable: {exc}",
            )

    def list_run_steps(self, run_id: int) -> RunStepsPayload:
        try:
            rows = database.fetch_all(
                """
                SELECT
                    id, job_run_id, step_code, step_name, attempt_no, status,
                    article_id, error_message, detail_json, started_at, finished_at, updated_at
                FROM geo_job_steps
                WHERE job_run_id = %s
                ORDER BY started_at ASC, attempt_no ASC, id ASC
                """,
                params=(run_id,),
            )
            return RunStepsPayload(
                run_id=run_id,
                items=[_map_step(row) for row in rows],
                warning=None,
            )
        except Exception as exc:
            return RunStepsPayload(
                run_id=run_id,
                items=[],
                warning=f"run_steps_unavailable: {exc}",
            )


runs_service = RunsService()
