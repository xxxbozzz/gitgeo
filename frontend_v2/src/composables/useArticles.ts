import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import { computed, toValue, type MaybeRefOrGetter } from 'vue'

import {
  fetchArticleDetail,
  fetchArticles,
  fetchArticlesSummary,
  postArticlePublish,
  postArticleRecycle,
  postArticleRefix,
} from '../api/articles'
import type { ArticleListFilters, ArticlePublishRequest } from '../types/articles'
import { queryKeys } from './queryKeys'

const DEFAULT_ARTICLE_FILTERS: ArticleListFilters = {
  min_score: 0,
  limit: 20,
  offset: 0,
}

export function useArticlesQuery(
  filters: MaybeRefOrGetter<ArticleListFilters> = DEFAULT_ARTICLE_FILTERS,
) {
  const normalizedFilters = computed(() => ({
    ...DEFAULT_ARTICLE_FILTERS,
    ...(toValue(filters) ?? {}),
  }))

  return useQuery({
    queryKey: computed(() => queryKeys.articles.list(normalizedFilters.value)),
    queryFn: () => fetchArticles(normalizedFilters.value),
  })
}

export function useArticlesSummaryQuery() {
  return useQuery({
    queryKey: queryKeys.articles.summary,
    queryFn: fetchArticlesSummary,
  })
}

export function useArticleDetailQuery(
  articleId: MaybeRefOrGetter<number | null | undefined>,
) {
  const resolvedArticleId = computed(() => toValue(articleId) ?? null)

  return useQuery({
    queryKey: computed(() => queryKeys.articles.detail(resolvedArticleId.value ?? 0)),
    queryFn: () => fetchArticleDetail(resolvedArticleId.value as number),
    enabled: computed(() => Boolean(resolvedArticleId.value)),
  })
}

export function useArticleRefixMutation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (articleId: number) => postArticleRefix(articleId),
    onSuccess: (_data, articleId) => {
      queryClient.invalidateQueries({ queryKey: ['articles'] })
      queryClient.invalidateQueries({ queryKey: queryKeys.articles.detail(articleId) })
      queryClient.invalidateQueries({ queryKey: ['overview'] })
      queryClient.invalidateQueries({ queryKey: ['runs'] })
    },
  })
}

export function useArticleRecycleMutation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (articleId: number) => postArticleRecycle(articleId),
    onSuccess: (_data, articleId) => {
      queryClient.invalidateQueries({ queryKey: ['articles'] })
      queryClient.removeQueries({ queryKey: queryKeys.articles.detail(articleId) })
      queryClient.invalidateQueries({ queryKey: ['overview'] })
      queryClient.invalidateQueries({ queryKey: ['runs'] })
      queryClient.invalidateQueries({ queryKey: ['publications'] })
    },
  })
}

export function useArticlePublishMutation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      articleId,
      payload,
    }: {
      articleId: number
      payload: ArticlePublishRequest
    }) => postArticlePublish(articleId, payload),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['articles'] })
      queryClient.invalidateQueries({
        queryKey: queryKeys.articles.detail(variables.articleId),
      })
      queryClient.invalidateQueries({ queryKey: ['publications'] })
      queryClient.invalidateQueries({ queryKey: ['overview'] })
    },
  })
}
