import { getData } from './http'
import type {
  LatestArticlesPayload,
  OverviewBoardPayload,
  OverviewKpisPayload,
  OverviewTrendPayload,
} from '../types/overview'

export function fetchOverviewKpis() {
  return getData<OverviewKpisPayload>('/overview/kpis')
}

export function fetchOverviewTrend(days = 7) {
  return getData<OverviewTrendPayload>('/overview/trend', {
    params: { days },
  })
}

export function fetchOverviewBoard(pendingLimit = 5, articleLimit = 5) {
  return getData<OverviewBoardPayload>('/overview/board', {
    params: {
      pending_limit: pendingLimit,
      article_limit: articleLimit,
    },
  })
}

export function fetchLatestArticles(limit = 8) {
  return getData<LatestArticlesPayload>('/overview/latest-articles', {
    params: { limit },
  })
}
