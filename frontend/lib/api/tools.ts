import { apiFetch } from "./client";
import { ToolRow, ToolExecutionRow } from "../types/backend";

export interface ToolStats {
  totalTools: number;
  activeTools: number;
  totalExecutions: number;
  successRate: number;
}

export const toolsApi = {
  listTools: async (): Promise<ToolRow[]> => {
    const data = await apiFetch<{ items?: ToolRow[] } | ToolRow[]>("/api/tools", { method: "GET" });
    // Handle both array and paginated response shapes
    if (Array.isArray(data)) return data;
    return (data as any).items || [];
  },

  getTool: async (toolId: string): Promise<ToolRow> => {
    return apiFetch<ToolRow>(`/api/tools/${toolId}`, { method: "GET" });
  },

  getToolExecutions: async (toolId: string, limit: number = 20): Promise<ToolExecutionRow[]> => {
    const data = await apiFetch<{ items?: ToolExecutionRow[] } | ToolExecutionRow[]>(
      `/api/tools/${toolId}/executions?limit=${limit}`,
      { method: "GET" }
    );
    if (Array.isArray(data)) return data;
    return (data as any).items || [];
  },

  registerTool: async (payload: { name: string; category: string; description: string }): Promise<ToolRow> => {
    return apiFetch<ToolRow>("/api/tools", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
};
