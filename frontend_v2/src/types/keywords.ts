import type { PaginatedPayload } from './api'

export interface KeywordSummaryItem {
  id: number
  keyword: string
  target_article_id: number | null
  target_article_title: string | null
  target_article_slug: string | null
  search_volume: number
  difficulty: number
  cannibalization_risk: boolean
  status: 'pending' | 'consumed' | string
  created_at: string | null
}

export type KeywordListPayload = PaginatedPayload<KeywordSummaryItem>

export type GapKeywordListPayload = PaginatedPayload<KeywordSummaryItem>

export interface KeywordClusterItem {
  cluster_name: string
  keywords_total: number
  pending_keywords: number
  consumed_keywords: number
  average_difficulty: number | null
}

export interface KeywordClustersPayload {
  items: KeywordClusterItem[]
  limit: number
  warning: string | null
}

export interface KeywordListFilters {
  status?: string
  query?: string
  limit?: number
  offset?: number
}

export interface GapKeywordFilters {
  query?: string
  limit?: number
  offset?: number
}
