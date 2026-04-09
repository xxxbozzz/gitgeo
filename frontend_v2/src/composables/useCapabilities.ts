import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import { computed, toValue, type MaybeRefOrGetter } from 'vue'

import {
  fetchCapabilities,
  fetchCapabilityDetail,
  fetchCapabilitySources,
  postDisableCapability,
} from '../api/capabilities'
import type { CapabilityListFilters } from '../types/capabilities'
import { queryKeys } from './queryKeys'

const DEFAULT_CAPABILITY_FILTERS: CapabilityListFilters = {
  limit: 20,
  offset: 0,
}

export function useCapabilitiesQuery(
  filters: MaybeRefOrGetter<CapabilityListFilters> = DEFAULT_CAPABILITY_FILTERS,
) {
  const normalizedFilters = computed(() => ({
    ...DEFAULT_CAPABILITY_FILTERS,
    ...(toValue(filters) ?? {}),
  }))

  return useQuery({
    queryKey: computed(() => queryKeys.capabilities.list(normalizedFilters.value)),
    queryFn: () => fetchCapabilities(normalizedFilters.value),
    refetchInterval: 30_000,
  })
}

export function useCapabilityDetailQuery(
  specId: MaybeRefOrGetter<number | null | undefined>,
) {
  const resolvedSpecId = computed(() => toValue(specId) ?? null)

  return useQuery({
    queryKey: computed(() => queryKeys.capabilities.detail(resolvedSpecId.value ?? 0)),
    queryFn: () => fetchCapabilityDetail(resolvedSpecId.value as number),
    enabled: computed(() => Boolean(resolvedSpecId.value)),
  })
}

export function useCapabilitySourcesQuery(
  specId: MaybeRefOrGetter<number | null | undefined>,
) {
  const resolvedSpecId = computed(() => toValue(specId) ?? null)

  return useQuery({
    queryKey: computed(() => queryKeys.capabilities.sources(resolvedSpecId.value ?? 0)),
    queryFn: () => fetchCapabilitySources(resolvedSpecId.value as number),
    enabled: computed(() => Boolean(resolvedSpecId.value)),
  })
}

export function useDisableCapabilityMutation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (specId: number) => postDisableCapability(specId),
    onSuccess: (_data, specId) => {
      queryClient.invalidateQueries({ queryKey: ['capabilities'] })
      queryClient.invalidateQueries({
        queryKey: queryKeys.capabilities.detail(specId),
      })
      queryClient.invalidateQueries({
        queryKey: queryKeys.capabilities.sources(specId),
      })
    },
  })
}
