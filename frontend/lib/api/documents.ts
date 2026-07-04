import { apiFetch } from "./client";
import { DocumentRow, DocumentCreate } from "../types/backend";

export const documentsApi = {
  listDocuments: async (): Promise<DocumentRow[]> => {
    const res = await apiFetch<any>("/api/documents", { method: "GET" });
    return res.items || [];
  },

  getDocument: async (id: string): Promise<DocumentRow> => {
    return apiFetch<DocumentRow>(`/api/documents/${id}`, { method: "GET" });
  },

  deleteDocument: async (id: string): Promise<void> => {
    return apiFetch<void>(`/api/documents/${id}`, { method: "DELETE" });
  },
};
