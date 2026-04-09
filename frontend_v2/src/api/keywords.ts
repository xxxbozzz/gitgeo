import { getData } from './http'
import type {
  GapKeywordFilters,
  GapKeywordListPayload,
  KeywordClustersPayload,
  KeywordListFilters,
  KeywordListPayload,
} from '../types/keywords'

export function fetchKeywords(filters: KeywordListFilters = {}) {
  return getData<KeywordListPayload>('/keywords', {
    params: filters,
  })
}

export function fetchGapKeywords(filters: GapKeywordFilters = {}) {
  return getData<GapKeywordListPayload>('/gap-keywords', {
    params: filters,
  })
}

export function fetchKeywordClusters(limit = 12) {
  return getData<KeywordClustersPayload>('/keywords/clusters', {
    params: { limit },
  })
}
