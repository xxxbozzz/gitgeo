import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import { computed, toValue, type MaybeRefOrGetter } from 'vue'

import {
  fetchPublicationDetail,
  fetchPublications,
  postRetryPublication,
} from '../api/publications'
import type { PublicationListFilters } from '../types/publications'
import { queryKeys } from './queryKeys'

const DEFAULT_PUBLICATION_FILTERS: PublicationListFilters = {
  limit: 20,
  offset: 0,
}

export function usePublicationsQuery(
  filters: MaybeRefOrGetter<PublicationListFilters> = DEFAULT_PUBLICATION_FILTERS,
) {
  const normalizedFilters = computed(() => ({
    ...DEFAULT_PUBLICATION_FILTERS,
    ...(toValue(filters) ?? {}),
  }))

  return useQuery({
    queryKey: computed(() => queryKeys.publications.list(normalizedFilters.value)),
    queryFn: () => fetchPublications(normalizedFilters.value),
  })
}

export function usePublicationDetailQuery(
  publicationId: MaybeRefOrGetter<number | null | undefined>,
) {
  const resolvedPublicationId = computed(() => toValue(publicationId) ?? null)

  return useQuery({
    queryKey: computed(() => queryKeys.publications.detail(resolvedPublicationId.value ?? 0)),
    queryFn: () => fetchPublicationDetail(resolvedPublicationId.value as number),
    enabled: computed(() => Boolean(resolvedPublicationId.value)),
  })
}

export function useRetryPublicationMutation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (publicationId: number) => postRetryPublication(publicationId),
    onSuccess: (_data, publicationId) => {
      queryClient.invalidateQueries({ queryKey: ['publications'] })
      queryClient.invalidateQueries({
        queryKey: queryKeys.publications.detail(publicationId),
      })
      queryClient.invalidateQueries({ queryKey: ['articles'] })
      queryClient.invalidateQueries({ queryKey: ['overview'] })
    },
  })
}
