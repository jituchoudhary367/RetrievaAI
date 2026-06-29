import { apiFetch } from "./client";
import { ToolRow, ToolExecutionRow } from "../types/backend";

export const toolsApi = {
  listTools: async (): Promise<ToolRow[]> => {
    return apiFetch<ToolRow[]>("/api/v1/tools", { method: "GET" });
  },

  getToolExecutions: async (toolId: string, limit: number = 50): Promise<ToolExecutionRow[]> => {
    return apiFetch<ToolExecutionRow[]>(`/api/v1/tools/${toolId}/executions?limit=${limit}`, { method: "GET" });
  }
};
