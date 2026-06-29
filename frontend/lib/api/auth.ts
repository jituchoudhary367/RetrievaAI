import { apiFetch } from "./client";
import { TokenResponse, User } from "../types/backend";

export const authApi = {
  login: async (formData: FormData): Promise<TokenResponse> => {
    return apiFetch<TokenResponse>("/api/v1/auth/token", {
      method: "POST",
      body: formData,
    });
  },

  getCurrentUser: async (): Promise<User> => {
    return apiFetch<User>("/api/v1/auth/me", {
      method: "GET",
    });
  },
};
