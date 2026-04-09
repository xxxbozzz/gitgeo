import { getData, postData } from './http'
import type {
  PublicationDetailPayload,
  PublicationListFilters,
  PublicationListPayload,
  PublicationRetryResult,
} from '../types/publications'

export function fetchPublications(filters: PublicationListFilters = {}) {
  return getData<PublicationListPayload>('/publications', {
    params: filters,
  })
}

export function fetchPublicationDetail(publicationId: number) {
  return getData<PublicationDetailPayload>(`/publications/${publicationId}`)
}

export function postRetryPublication(publicationId: number) {
  return postData<PublicationRetryResult>(`/publications/${publicationId}/retry`)
}
