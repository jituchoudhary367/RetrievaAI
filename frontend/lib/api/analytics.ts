import { apiFetch } from "./client";

export interface DetailedMetrics {
  retrieval_analytics: {
    avg_retrieved_chunks: number;
    avg_context_tokens: number;
    avg_documents_used: number;
    avg_citation_count: number;
    cache_hit_rate: number;
    web_search_triggered: number;
  };
  query_pipeline: {
    rewrite_ms: number;
    retrieve_ms: number;
    rerank_ms: number;
    generate_ms: number;
    total_ms: number;
  };
  llm_usage: {
    provider: string;
    models_used: string;
    average_tokens: number;
    prompt_tokens: number;
    completion_tokens: number;
    average_cost_usd: number;
  };
  retrieval_quality: {
    avg_retrieval_score: number;
    avg_crossencoder_score: number;
    low_confidence_answers: number;
    hallucination_prevented: number;
    need_web_trigger: number;
  };
  document_insights: {
    indexed: number;
    chunks: number;
    avg_chunks: number;
    largest_document: string;
    duplicate_chunks_removed: number;
    avg_chunk_size_tokens: number;
  };
  search_intent_distribution: { intent: string; count: number }[];
  popular_documents: { title: string; queries: number }[];
  slow_queries: { query: string; latency: string }[];
  activity_heatmap: { day: string; count: number }[];
  retrieval_sources: { source: string; percentage: number }[];
}

export interface AnalyticsOverview {
  totalQueries: number;
  activeUsers: number;
  avgLatencyMs: number;
  documentsIndexed: number;
  totalChunks: number;
}

// Normalise backend snake_case → camelCase
function normaliseOverview(raw: any): AnalyticsOverview {
  return {
    totalQueries: raw.total_queries ?? raw.totalQueries ?? 0,
    activeUsers: raw.active_users ?? raw.activeUsers ?? 0,
    avgLatencyMs: raw.avg_latency_ms ?? raw.averageLatencyMs ?? 0,
    documentsIndexed: raw.documents_indexed ?? raw.documentsIndexed ?? 0,
    totalChunks: raw.total_chunks ?? raw.totalChunks ?? 0,
  };
}

export const analyticsApi = {
  // Main overview stats
  getOverview: async (days: number = 30): Promise<AnalyticsOverview> => {
    const raw = await apiFetch<any>(`/api/analytics/overview?days=${days}`, { method: "GET" });
    return normaliseOverview(raw);
  },

  // Daily query counts — returns [{date, count}]
  getQueryDistribution: async (days: number = 7): Promise<any[]> => {
    const data = await apiFetch<any[]>(`/api/analytics/query-distribution?days=${days}`, { method: "GET" });
    return Array.isArray(data) ? data : [];
  },

  // Most recent queries
  getTopQueries: async (limit: number = 10): Promise<any[]> => {
    const data = await apiFetch<any[]>(`/api/analytics/top-queries?limit=${limit}`, { method: "GET" });
    return Array.isArray(data) ? data : [];
  },

  // Latest EvalRun metrics
  getRetrievalQuality: async (): Promise<any> => {
    return apiFetch<any>("/api/analytics/retrieval-quality", { method: "GET" });
  },

  // System health samples
  getSystemHealth: async (limit: number = 60): Promise<any[]> => {
    const data = await apiFetch<any[]>(`/api/analytics/system-health?limit=${limit}`, { method: "GET" });
    return Array.isArray(data) ? data : [];
  },

  // Detailed Metrics for new UI
  getDetailedMetrics: async (days: number = 30): Promise<DetailedMetrics> => {
    return apiFetch<DetailedMetrics>(`/api/analytics/detailed-metrics?days=${days}`, { method: "GET" });
  },
};
