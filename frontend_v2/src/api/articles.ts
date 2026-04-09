import { getData, postData } from './http'
import type {
  ArticleDetailPayload,
  ArticleListFilters,
  ArticleListPayload,
  ArticleMutationResult,
  ArticlePublishRequest,
  ArticleSummaryPayload,
} from '../types/articles'

export function fetchArticles(filters: ArticleListFilters = {}) {
  return getData<ArticleListPayload>('/articles', {
    params: filters,
  })
}

export function fetchArticlesSummary() {
  return getData<ArticleSummaryPayload>('/articles/summary')
}

export function fetchArticleDetail(articleId: number) {
  return getData<ArticleDetailPayload>(`/articles/${articleId}`)
}

export function postArticleRefix(articleId: number) {
  return postData<ArticleMutationResult>(`/articles/${articleId}/refix`)
}

export function postArticleRecycle(articleId: number) {
  return postData<ArticleMutationResult>(`/articles/${articleId}/recycle`)
}

export function postArticlePublish(articleId: number, payload: ArticlePublishRequest) {
  return postData<ArticleMutationResult, ArticlePublishRequest>(
    `/articles/${articleId}/publish`,
    payload,
  )
}
