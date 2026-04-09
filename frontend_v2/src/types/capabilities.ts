import type { PaginatedPayload } from './api'

export interface CapabilityArticleReference {
  id: number
  title: string
  slug: string
  publish_status: number
  quality_score: number
  updated_at: string | null
}

export interface CapabilitySummaryItem {
  id: number
  group_code: string
  group_name: string
  capability_code: string
  capability_name: string
  category: string | null
  public_claim: string | null
  claim_level: string
  confidence_score: number
  is_active: boolean
  source_count: number
  application_tags: string[]
  updated_at: string | null
}

export interface CapabilityDetailItem extends CapabilitySummaryItem {
  metric_type: string
  unit: string | null
  comparator: string | null
  conservative_value_num: number | null
  conservative_value_text: string | null
  advanced_value_num: number | null
  advanced_value_text: string | null
  internal_note: string | null
  conditions_text: string | null
  recent_articles: CapabilityArticleReference[]
}

export interface CapabilitySourceItem {
  id: number
  source_code: string
  source_vendor: string
  source_title: string
  source_type: string
  source_url: string
  publish_org: string | null
  observed_on: string | null
  reliability_score: number
  citation_note: string | null
  priority_weight: number
}

export interface CapabilityListPayload extends PaginatedPayload<CapabilitySummaryItem> {
  active_total: number
  inactive_total: number
  groups_total: number
}

export interface CapabilityDetailPayload {
  capability: CapabilityDetailItem | null
  warning: string | null
}

export interface CapabilitySourcesPayload {
  spec_id: number
  items: CapabilitySourceItem[]
  warning: string | null
}

export interface CapabilityListFilters {
  active?: boolean
  group_code?: string
  query?: string
  limit?: number
  offset?: number
}

export type CapabilityDisableResult = Record<string, unknown>
