import type { PaginatedPayload } from './api'

export interface ArticleSummaryItem {
  id: number
  title: string
  slug: string
  quality_score: number
  publish_status: number
  dim_subject: string | null
  dim_action: string | null
  dim_attribute: string | null
  created_at: string | null
  updated_at: string | null
}

export interface ArticleDetailItem extends ArticleSummaryItem {
  meta_json: Record<string, unknown> | unknown[] | null
  content_markdown: string | null
  target_keywords: string[]
  outgoing_links_count: number
  incoming_links_count: number
  related_run_id: number | null
  related_run_status: string | null
}

export type ArticleListPayload = PaginatedPayload<ArticleSummaryItem>

export interface ArticleSummaryPayload {
  total_articles: number
  draft_articles: number
  approved_articles: number
  published_articles: number
  average_quality_score: number | null
  warning: string | null
}

export interface ArticleDetailPayload {
  article: ArticleDetailItem | null
  warning: string | null
}

export interface ArticleListFilters {
  status?: string
  min_score?: number
  query?: string
  limit?: number
  offset?: number
}

export interface ArticlePublishRequest {
  channels: Array<'longform_channel' | 'mobile_channel'>
  go_live: boolean
}

export type ArticleMutationResult = Record<string, unknown>
