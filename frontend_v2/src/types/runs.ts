import type { PaginatedPayload } from './api'

export interface RunSummaryItem {
  id: number
  run_uid: string
  run_type: string
  trigger_mode: string
  keyword_id: number | null
  keyword: string
  article_id: number | null
  status: string
  current_step: string | null
  retry_count: number
  error_message: string | null
  detail_json: Record<string, unknown> | unknown[] | null
  started_at: string | null
  finished_at: string | null
  updated_at: string | null
}

export interface RunStepItem {
  id: number
  job_run_id: number
  step_code: string
  step_name: string
  attempt_no: number
  status: string
  article_id: number | null
  error_message: string | null
  detail_json: Record<string, unknown> | unknown[] | null
  started_at: string | null
  finished_at: string | null
  updated_at: string | null
}

export type RunListPayload = PaginatedPayload<RunSummaryItem>

export interface RunSummaryPayload {
  total_runs: number
  running_runs: number
  succeeded_runs: number
  failed_runs: number
  partial_runs: number
  latest_run_at: string | null
  warning: string | null
}

export interface RunFailuresPayload {
  items: RunSummaryItem[]
  limit: number
  warning: string | null
}

export interface RunDetailPayload {
  run: RunSummaryItem | null
  steps_total: number
  failed_steps: number
  warning: string | null
}

export interface RunStepsPayload {
  run_id: number
  items: RunStepItem[]
  warning: string | null
}

export interface RunListFilters {
  status?: string
  trigger_mode?: string
  keyword?: string
  limit?: number
  offset?: number
}
