import type { ArticleListFilters } from '../types/articles'
import type { CapabilityListFilters } from '../types/capabilities'
import type { GapKeywordFilters, KeywordListFilters } from '../types/keywords'
import type { PublicationListFilters } from '../types/publications'
import type { RunListFilters } from '../types/runs'

export const queryKeys = {
  overview: {
    kpis: ['overview', 'kpis'] as const,
    trend: (days: number) => ['overview', 'trend', days] as const,
    board: (pendingLimit: number, articleLimit: number) =>
      ['overview', 'board', pendingLimit, articleLimit] as const,
    latestArticles: (limit: number) => ['overview', 'latest-articles', limit] as const,
  },
  articles: {
    list: (filters: ArticleListFilters) => ['articles', filters] as const,
    summary: ['articles', 'summary'] as const,
    detail: (articleId: number) => ['article', articleId] as const,
  },
  runs: {
    list: (filters: RunListFilters) => ['runs', filters] as const,
    summary: ['runs', 'summary'] as const,
    recentFailures: (limit: number) => ['runs', 'recent-failures', limit] as const,
    detail: (runId: number) => ['run', runId] as const,
    steps: (runId: number) => ['run-steps', runId] as const,
  },
  publications: {
    list: (filters: PublicationListFilters) => ['publications', filters] as const,
    detail: (publicationId: number) => ['publication', publicationId] as const,
  },
  keywords: {
    list: (filters: KeywordListFilters) => ['keywords', filters] as const,
    gap: (filters: GapKeywordFilters) => ['gap-keywords', filters] as const,
    clusters: (limit: number) => ['keywords-clusters', limit] as const,
  },
  capabilities: {
    list: (filters: CapabilityListFilters) => ['capabilities', filters] as const,
    detail: (specId: number) => ['capability', specId] as const,
    sources: (specId: number) => ['capability-sources', specId] as const,
  },
  system: {
    status: ['system', 'status'] as const,
  },
}
