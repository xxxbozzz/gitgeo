import { getData } from './http'
import type {
  RunDetailPayload,
  RunFailuresPayload,
  RunListFilters,
  RunListPayload,
  RunStepsPayload,
  RunSummaryPayload,
} from '../types/runs'

export function fetchRuns(filters: RunListFilters = {}) {
  return getData<RunListPayload>('/runs', {
    params: filters,
  })
}

export function fetchRunsSummary() {
  return getData<RunSummaryPayload>('/runs/summary')
}

export function fetchRecentRunFailures(limit = 10) {
  return getData<RunFailuresPayload>('/runs/recent-failures', {
    params: { limit },
  })
}

export function fetchRunDetail(runId: number) {
  return getData<RunDetailPayload>(`/runs/${runId}`)
}

export function fetchRunSteps(runId: number) {
  return getData<RunStepsPayload>(`/runs/${runId}/steps`)
}
