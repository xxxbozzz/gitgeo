import { useQuery } from '@tanstack/vue-query'

import {
  fetchLatestArticles,
  fetchOverviewBoard,
  fetchOverviewKpis,
  fetchOverviewTrend,
} from '../api/overview'
import { queryKeys } from './queryKeys'

export function useOverviewKpisQuery() {
  return useQuery({
    queryKey: queryKeys.overview.kpis,
    queryFn: fetchOverviewKpis,
  })
}

export function useOverviewTrendQuery(days = 7) {
  return useQuery({
    queryKey: queryKeys.overview.trend(days),
    queryFn: () => fetchOverviewTrend(days),
  })
}

export function useOverviewBoardQuery(pendingLimit = 5, articleLimit = 5) {
  return useQuery({
    queryKey: queryKeys.overview.board(pendingLimit, articleLimit),
    queryFn: () => fetchOverviewBoard(pendingLimit, articleLimit),
  })
}

export function useLatestArticlesQuery(limit = 8) {
  return useQuery({
    queryKey: queryKeys.overview.latestArticles(limit),
    queryFn: () => fetchLatestArticles(limit),
  })
}
