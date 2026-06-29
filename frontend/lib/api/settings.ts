import { apiFetch } from "./client";
import { SystemSettings } from "../types/backend";

export const settingsApi = {
  getSettings: async (): Promise<SystemSettings> => {
    return apiFetch<SystemSettings>("/api/v1/settings", { method: "GET" });
  },

  updateSettings: async (settings: Partial<SystemSettings>): Promise<SystemSettings> => {
    return apiFetch<SystemSettings>("/api/v1/settings", { 
      method: "PATCH",
      body: JSON.stringify(settings)
    });
  }
};
