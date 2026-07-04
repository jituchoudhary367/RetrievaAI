import { apiFetch } from "./client";

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
};
