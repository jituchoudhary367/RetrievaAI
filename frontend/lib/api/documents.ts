import { apiFetch } from "./client";
import { DocumentRow, DocumentCreate } from "../types/backend";

export const documentsApi = {
  listDocuments: async (): Promise<DocumentRow[]> => {
    return apiFetch<DocumentRow[]>("/api/v1/documents", { method: "GET" });
  },

  getDocument: async (id: string): Promise<DocumentRow> => {
    return apiFetch<DocumentRow>(`/api/v1/documents/${id}`, { method: "GET" });
  },

  deleteDocument: async (id: string): Promise<void> => {
    return apiFetch<void>(`/api/v1/documents/${id}`, { method: "DELETE" });
  },
};
