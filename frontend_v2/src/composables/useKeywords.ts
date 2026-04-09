import { useQuery } from '@tanstack/vue-query'
import { computed, toValue, type MaybeRefOrGetter } from 'vue'

import { fetchGapKeywords, fetchKeywordClusters, fetchKeywords } from '../api/keywords'
import type { GapKeywordFilters, KeywordListFilters } from '../types/keywords'
import { queryKeys } from './queryKeys'

const DEFAULT_KEYWORD_FILTERS: KeywordListFilters = {
  limit: 20,
  offset: 0,
}

const DEFAULT_GAP_KEYWORD_FILTERS: GapKeywordFilters = {
  limit: 10,
  offset: 0,
}

export function useKeywordsQuery(
  filters: MaybeRefOrGetter<KeywordListFilters> = DEFAULT_KEYWORD_FILTERS,
) {
  const normalizedFilters = computed(() => ({
    ...DEFAULT_KEYWORD_FILTERS,
    ...(toValue(filters) ?? {}),
  }))

  return useQuery({
    queryKey: computed(() => queryKeys.keywords.list(normalizedFilters.value)),
    queryFn: () => fetchKeywords(normalizedFilters.value),
    refetchInterval: 30_000,
  })
}

export function useGapKeywordsQuery(
  filters: MaybeRefOrGetter<GapKeywordFilters> = DEFAULT_GAP_KEYWORD_FILTERS,
) {
  const normalizedFilters = computed(() => ({
    ...DEFAULT_GAP_KEYWORD_FILTERS,
    ...(toValue(filters) ?? {}),
  }))

  return useQuery({
    queryKey: computed(() => queryKeys.keywords.gap(normalizedFilters.value)),
    queryFn: () => fetchGapKeywords(normalizedFilters.value),
    refetchInterval: 30_000,
  })
}

export function useKeywordClustersQuery(limit: MaybeRefOrGetter<number> = 12) {
  const normalizedLimit = computed(() => toValue(limit))

  return useQuery({
    queryKey: computed(() => queryKeys.keywords.clusters(normalizedLimit.value)),
    queryFn: () => fetchKeywordClusters(normalizedLimit.value),
    refetchInterval: 30_000,
  })
}
