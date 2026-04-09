import { useQuery } from '@tanstack/vue-query'

import { fetchSystemStatus } from '../api/system'
import { queryKeys } from './queryKeys'

export function useSystemStatusQuery() {
  return useQuery({
    queryKey: queryKeys.system.status,
    queryFn: fetchSystemStatus,
    refetchInterval: 30_000,
  })
}
