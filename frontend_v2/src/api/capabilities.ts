import { getData, postData } from './http'
import type {
  CapabilityDetailPayload,
  CapabilityDisableResult,
  CapabilityListFilters,
  CapabilityListPayload,
  CapabilitySourcesPayload,
} from '../types/capabilities'

export function fetchCapabilities(filters: CapabilityListFilters = {}) {
  return getData<CapabilityListPayload>('/capabilities', {
    params: filters,
  })
}

export function fetchCapabilityDetail(specId: number) {
  return getData<CapabilityDetailPayload>(`/capabilities/${specId}`)
}

export function fetchCapabilitySources(specId: number) {
  return getData<CapabilitySourcesPayload>(`/capabilities/${specId}/sources`)
}

export function postDisableCapability(specId: number) {
  return postData<CapabilityDisableResult>(`/capabilities/${specId}/disable`)
}
