import { apiFetch } from "./client";

export interface NotificationRow {
  id: string;
  userId: string;
  tenantId: string;
  type: string;
  title: string;
  message: string;
  isRead: boolean;
  createdAt: string;
}

export const notificationsApi = {
  listNotifications: async (unreadOnly: boolean = false): Promise<NotificationRow[]> => {
    return apiFetch<NotificationRow[]>(`/api/notifications?unread_only=${unreadOnly}`, { method: "GET" });
  },

  markAsRead: async (id: string): Promise<void> => {
    return apiFetch<void>(`/api/notifications/${id}/read`, { method: "POST" });
  },

  markAllAsRead: async (): Promise<void> => {
    return apiFetch<void>("/api/notifications/read-all", { method: "POST" });
  }
};
