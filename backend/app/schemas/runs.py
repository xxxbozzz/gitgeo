"""Run-related schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class RunSummaryItem(BaseModel):
    """Single runtime record."""

    id: int
    run_uid: str
    run_type: str
    trigger_mode: str
    keyword_id: int | None = None
    keyword: str
    article_id: int | None = None
    status: str
    current_step: str | None = None
    retry_count: int
    error_message: str | None = None
    detail_json: dict[str, Any] | list[Any] | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    updated_at: datetime | None = None


class RunStepItem(BaseModel):
    """Single runtime step."""

    id: int
    job_run_id: int
    step_code: str
    step_name: str
    attempt_no: int
    status: str
    article_id: int | None = None
    error_message: str | None = None
    detail_json: dict[str, Any] | list[Any] | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    updated_at: datetime | None = None


class RunListPayload(BaseModel):
    """Paginated run list payload."""

    items: list[RunSummaryItem] = Field(default_factory=list)
    total: int
    limit: int
    offset: int
    warning: str | None = None


class RunSummaryPayload(BaseModel):
    """Aggregated run summary."""

    total_runs: int
    running_runs: int
    succeeded_runs: int
    failed_runs: int
    partial_runs: int
    latest_run_at: datetime | None = None
    warning: str | None = None


class RunFailuresPayload(BaseModel):
    """Recent failures payload."""

    items: list[RunSummaryItem] = Field(default_factory=list)
    limit: int
    warning: str | None = None


class RunDetailPayload(BaseModel):
    """Detailed run payload."""

    run: RunSummaryItem | None = None
    steps_total: int = 0
    failed_steps: int = 0
    warning: str | None = None


class RunStepsPayload(BaseModel):
    """Single run steps payload."""

    run_id: int
    items: list[RunStepItem] = Field(default_factory=list)
    warning: str | None = None
