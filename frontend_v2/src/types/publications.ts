import type { PaginatedPayload } from './api'

export interface PublicationSummaryItem {
  id: number
  article_id: number
  article_title: string | null
  article_slug: string | null
  article_publish_status: number | null
  channel_key: string
  channel_label: string
  adapter_key: string
  adapter_label: string
  publish_mode: string
  status: string
  trigger_mode: string
  attempt_no: number
  retry_of_publication_id: number | null
  retryable: boolean
  external_id: string | null
  external_url: string | null
  message: string | null
  error_message: string | null
  published_at: string | null
  created_at: string | null
  updated_at: string | null
}

export interface PublicationDetailItem extends PublicationSummaryItem {
  request_payload_json: Record<string, unknown> | unknown[] | null
  response_payload_json: Record<string, unknown> | unknown[] | null
  retry_attempts_total: number
}

export type PublicationListPayload = PaginatedPayload<PublicationSummaryItem>

export interface PublicationDetailPayload {
  publication: PublicationDetailItem | null
  warning: string | null
}

export interface PublicationListFilters {
  article_id?: number
  channel?: string
  status?: string
  trigger_mode?: string
  query?: string
  limit?: number
  offset?: number
}

export type PublicationRetryResult = Record<string, unknown>
