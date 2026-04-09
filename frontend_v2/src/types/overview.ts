import type { ArticleSummaryItem } from './articles'

export interface OverviewKpisPayload {
  articles_total: number
  passed_articles: number
  pending_keywords: number
  average_quality_score: number | null
  internal_links: number
  latest_article_at: string | null
  warning: string | null
}

export interface OverviewTrendPoint {
  day: string | null
  count: number
}

export interface OverviewTrendPayload {
  days: number
  items: OverviewTrendPoint[]
  warning: string | null
}

export interface PendingKeywordItem {
  id: number
  keyword: string
  search_volume: number
  difficulty: number
}

export interface OverviewBoardPayload {
  pending_keywords: PendingKeywordItem[]
  draft_articles: ArticleSummaryItem[]
  ready_articles: ArticleSummaryItem[]
  warning: string | null
}

export interface LatestArticlesPayload {
  items: ArticleSummaryItem[]
  limit: number
  warning: string | null
}
