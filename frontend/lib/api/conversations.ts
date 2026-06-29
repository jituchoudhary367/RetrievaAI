import { apiFetch } from "./client";
import { ConversationRow, ConversationMessageRow } from "../types/backend";

export const conversationsApi = {
  listConversations: async (): Promise<ConversationRow[]> => {
    return apiFetch<ConversationRow[]>("/api/v1/conversations", { method: "GET" });
  },

  getConversationHistory: async (sessionId: string): Promise<ConversationMessageRow[]> => {
    return apiFetch<ConversationMessageRow[]>(`/api/v1/conversations/${sessionId}/history`, { method: "GET" });
  },

  deleteConversation: async (sessionId: string): Promise<void> => {
    return apiFetch<void>(`/api/v1/conversations/${sessionId}`, { method: "DELETE" });
  }
};
