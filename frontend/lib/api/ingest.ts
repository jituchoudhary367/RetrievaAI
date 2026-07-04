import { apiFetch, apiBaseUrl } from "./client";
import { getAuthToken } from "../auth/session";

export interface IngestionJob {
  id: string;
  source_path_or_url: string;
  source_type?: string;
  status: string;
  progress_percent: number;
  chunks_total: number;
  chunks_indexed: number;
  error_message?: string;
  submitted_by?: string;
  started_at?: string;
  completed_at?: string;
  created_at: string;
}

export const ingestionApi = {
  listJobs: async (status?: string, limit: number = 20): Promise<{ items: IngestionJob[], total: number }> => {
    let url = `/api/ingestion/jobs?limit=${limit}`;
    if (status) url += `&status=${status}`;
    return apiFetch<any>(url, { method: "GET" });
  },

  getJob: async (id: string): Promise<IngestionJob> => {
    return apiFetch<IngestionJob>(`/api/ingestion/jobs/${id}`, { method: "GET" });
  },

  getJobChunks: async (id: string): Promise<any[]> => {
    return apiFetch<any[]>(`/api/ingestion/jobs/${id}/chunks`, { method: "GET" });
  },

  getJobMetadata: async (id: string): Promise<any> => {
    return apiFetch<any>(`/api/ingestion/jobs/${id}/metadata`, { method: "GET" });
  },

  submitJob: async (file: File, chunkSize?: number, chunkOverlap?: number): Promise<{ job_id: string, message: string }> => {
    const formData = new FormData();
    formData.append("file", file);
    if (chunkSize) formData.append("chunk_size", chunkSize.toString());
    if (chunkOverlap) formData.append("chunk_overlap", chunkOverlap.toString());

    const token = getAuthToken();
    const headers: Record<string, string> = {};
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const response = await fetch(`${apiBaseUrl}/api/ingestion/jobs`, {
      method: "POST",
      body: formData,
      headers,
    });

    if (!response.ok) {
      let errorMessage = "Failed to submit job";
      try {
        const errorData = await response.json();
        errorMessage = errorData.detail || errorMessage;
      } catch (e) {}
      throw new Error(errorMessage);
    }

    return response.json();
  },

  cancelJob: async (id: string): Promise<any> => {
    return apiFetch<any>(`/api/ingestion/jobs/${id}/cancel`, { method: "POST" });
  },

  deleteJob: async (id: string): Promise<void> => {
    return apiFetch<void>(`/api/ingestion/jobs/${id}`, { method: "DELETE" });
  }
};
