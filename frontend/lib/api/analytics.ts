import { apiFetch } from "./client";

export interface AnalyticsOverview {
  totalQueries: number;
  averageLatencyMs: number;
  cacheHitRate: number;
  activeUsers: number;
}

export const analyticsApi = {
  getOverview: async (timeRange: string = "7d"): Promise<AnalyticsOverview> => {
    return apiFetch<AnalyticsOverview>(`/api/v1/analytics/overview?time_range=${timeRange}`, { method: "GET" });
  },
  
  getSystemHealth: async (): Promise<any> => {
    return apiFetch<any>("/api/v1/analytics/health", { method: "GET" });
  }
};
