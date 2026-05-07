const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001/api/v1";

interface ApiEnvelope<T> { success: boolean; message: string; data: T | null; error_code: string | null }

async function get<T>(path: string, params?: Record<string, string | undefined>): Promise<T> {
  const url = new URL(BASE + path);
  if (params) Object.entries(params).forEach(([k, v]) => { if (v) url.searchParams.set(k, v) });
  const res = await fetch(url.toString(), { headers: { "Content-Type": "application/json" } });
  const json: ApiEnvelope<T> = await res.json();
  if (!json.success || !json.data) throw new Error(json.message || "API error");
  return json.data;
}

async function post<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(BASE + path, { method: "POST", headers: { "Content-Type": "application/json" }, body: body ? JSON.stringify(body) : undefined });
  const json: ApiEnvelope<T> = await res.json();
  if (!json.success) throw new Error(json.message || "API error");
  return json.data!;
}

// Types
export interface Article { id: number; title: string; slug: string; quality_score: number; publish_status: number; dim_subject?: string; dim_action?: string; dim_attribute?: string; created_at?: string; updated_at?: string; content_markdown?: string; meta_json?: unknown; target_keywords?: string[] }
export interface ArticlesList { items: Article[]; total: number; limit: number; offset: number }
export interface ArticlesSummary { total_articles: number; draft_articles: number; approved_articles: number; published_articles: number; average_quality_score: number }
export interface ArticleDetail { article: Article }

export interface Keyword { id: number; keyword: string; target_article_id?: number; search_volume: number; difficulty: number; status: string; created_at?: string }
export interface KeywordsList { items: Keyword[]; total: number; limit: number; offset: number }
export interface KeywordCluster { cluster_name: string; keywords_total: number; pending_keywords: number; consumed_keywords: number; average_difficulty?: number }
export interface KeywordsClusters { items: KeywordCluster[]; limit: number }

export interface Publication { id: number; article_id: number; article_title?: string; channel_key: string; channel_label: string; publish_mode: string; status: string; attempt_no: number; retryable: boolean; external_url?: string; error_message?: string; created_at?: string }
export interface PublicationsList { items: Publication[]; total: number; limit: number; offset: number }
export interface PublicationDetail { publication: Publication & { request_payload_json?: unknown; response_payload_json?: unknown } }

export interface Capability { id: number; group_code: string; group_name: string; capability_name: string; public_claim?: string; claim_level: string; confidence_score: number; is_active: boolean; source_count: number; application_tags: string[]; updated_at?: string }
export interface CapabilitiesList { items: Capability[]; total: number; limit: number; offset: number; active_total: number; inactive_total: number; groups_total: number }
export interface CapabilityDetail { capability: Capability & { conservative_value_text?: string; advanced_value_text?: string; conditions_text?: string; metric_type: string; recent_articles: Article[] } }
export interface CapabilitySource { id: number; source_code: string; source_vendor: string; source_title: string; source_type: string; source_url: string; reliability_score: number }
export interface CapabilitySources { spec_id: number; items: CapabilitySource[] }

export interface Run { id: number; run_uid: string; run_type: string; trigger_mode: string; keyword?: string; article_id?: number; status: string; current_step?: string; retry_count: number; error_message?: string; started_at?: string; finished_at?: string }
export interface RunsList { items: Run[]; total: number; limit: number; offset: number }
export interface RunSummary { total_runs: number; running_runs: number; succeeded_runs: number; failed_runs: number; partial_runs: number }
export interface RunDetail { run: Run; steps_total: number; failed_steps: number }
export interface RunStep { id: number; step_code: string; step_name: string; attempt_no: number; status: string; error_message?: string; started_at?: string; finished_at?: string }
export interface RunSteps { run_id: number; items: RunStep[] }

export interface Kpis { articles_total: number; passed_articles: number; pending_keywords: number; average_quality_score: number; internal_links: number; latest_article_at?: string }
export interface TrendItem { day: string; count: number }
export interface OverviewTrend { days: number; items: TrendItem[] }
export interface SystemStatus { environment: string; debug: boolean; database: string; llm_api_configured: boolean; build?: string }

// API functions
export const api = {
  overview: {
    kpis: () => get<Kpis>("/overview/kpis"),
    trend: (days = 7) => get<OverviewTrend>("/overview/trend", { days: String(days) }),
    board: () => get<{ pending_keywords: Keyword[]; draft_articles: Article[]; ready_articles: Article[] }>("/overview/board"),
    latestArticles: (limit = 8) => get<{ items: Article[] }>("/overview/latest-articles", { limit: String(limit) }),
  },
  articles: {
    list: (params?: Record<string, string>) => get<ArticlesList>("/articles", params),
    summary: () => get<ArticlesSummary>("/articles/summary"),
    detail: (id: number) => get<ArticleDetail>(`/articles/${id}`),
    refix: (id: number) => post(`/articles/${id}/refix`),
    recycle: (id: number) => post(`/articles/${id}/recycle`),
    publish: (id: number, channels: string[], goLive = false) => post(`/articles/${id}/publish`, { channels, go_live: goLive }),
  },
  keywords: {
    list: (params?: Record<string, string>) => get<KeywordsList>("/keywords", params),
    gap: (params?: Record<string, string>) => get<KeywordsList>("/gap-keywords", params),
    clusters: (limit = 12) => get<KeywordsClusters>("/keywords/clusters", { limit: String(limit) }),
  },
  publications: {
    list: (params?: Record<string, string>) => get<PublicationsList>("/publications", params),
    detail: (id: number) => get<PublicationDetail>(`/publications/${id}`),
    retry: (id: number) => post(`/publications/${id}/retry`),
  },
  capabilities: {
    list: (params?: Record<string, string>) => get<CapabilitiesList>("/capabilities", params),
    detail: (id: number) => get<CapabilityDetail>(`/capabilities/${id}`),
    sources: (id: number) => get<CapabilitySources>(`/capabilities/${id}/sources`),
    disable: (id: number) => post(`/capabilities/${id}/disable`),
  },
  runs: {
    list: (params?: Record<string, string>) => get<RunsList>("/runs", params),
    summary: () => get<RunSummary>("/runs/summary"),
    failures: (limit = 10) => get<{ items: Run[] }>("/runs/recent-failures", { limit: String(limit) }),
    detail: (id: number) => get<RunDetail>(`/runs/${id}`),
    steps: (id: number) => get<RunSteps>(`/runs/${id}/steps`),
  },
  system: {
    status: () => get<SystemStatus>("/system/status"),
    health: () => fetch(BASE.replace("/v1","") + "/health").then(r => r.json()),
    ready: () => fetch(BASE.replace("/v1","") + "/ready").then(r => r.json()),
  },
};
