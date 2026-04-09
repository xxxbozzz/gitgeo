import { useQuery } from '@tanstack/vue-query'
import { computed, toValue, type MaybeRefOrGetter } from 'vue'

import {
  fetchRecentRunFailures,
  fetchRunDetail,
  fetchRuns,
  fetchRunsSummary,
  fetchRunSteps,
} from '../api/runs'
import type { RunListFilters } from '../types/runs'
import { queryKeys } from './queryKeys'

const DEFAULT_RUN_FILTERS: RunListFilters = {
  limit: 20,
  offset: 0,
}

export function useRunsQuery(
  filters: MaybeRefOrGetter<RunListFilters> = DEFAULT_RUN_FILTERS,
) {
  const normalizedFilters = computed(() => ({
    ...DEFAULT_RUN_FILTERS,
    ...(toValue(filters) ?? {}),
  }))

  return useQuery({
    queryKey: computed(() => queryKeys.runs.list(normalizedFilters.value)),
    queryFn: () => fetchRuns(normalizedFilters.value),
  })
}

export function useRunsSummaryQuery() {
  return useQuery({
    queryKey: queryKeys.runs.summary,
    queryFn: fetchRunsSummary,
  })
}

export function useRecentRunFailuresQuery(limit = 10) {
  return useQuery({
    queryKey: queryKeys.runs.recentFailures(limit),
    queryFn: () => fetchRecentRunFailures(limit),
  })
}

export function useRunDetailQuery(
  runId: MaybeRefOrGetter<number | null | undefined>,
) {
  const resolvedRunId = computed(() => toValue(runId) ?? null)

  return useQuery({
    queryKey: computed(() => queryKeys.runs.detail(resolvedRunId.value ?? 0)),
    queryFn: () => fetchRunDetail(resolvedRunId.value as number),
    enabled: computed(() => Boolean(resolvedRunId.value)),
  })
}

export function useRunStepsQuery(
  runId: MaybeRefOrGetter<number | null | undefined>,
) {
  const resolvedRunId = computed(() => toValue(runId) ?? null)

  return useQuery({
    queryKey: computed(() => queryKeys.runs.steps(resolvedRunId.value ?? 0)),
    queryFn: () => fetchRunSteps(resolvedRunId.value as number),
    enabled: computed(() => Boolean(resolvedRunId.value)),
  })
}
