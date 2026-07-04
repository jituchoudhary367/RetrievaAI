import { apiFetch } from "./client";

export interface ApiKeyOut {
  id: string;
  name: string;
  prefix: string;
  lastUsedAt: string | null;
  createdAt: string;
}

export interface ApiKeyCreate {
  id: string;
  name: string;
  key: string; // shown once only
}

export interface SessionOut {
  id: string;
  ipAddress: string | null;
  userAgent: string | null;
  createdAt: string;
  lastSeenAt: string;
}

export interface AuditLogEntry {
  id: string;
  actorUserId: string | null;
  action: string;
  target: string | null;
  detail: Record<string, any> | null;
  createdAt: string;
}

export const settingsApi = {
  // Runtime settings
  getCategory: async (category: string): Promise<Record<string, any>> => {
    return apiFetch<Record<string, any>>(`/api/settings/${category}`, { method: "GET", cache: "no-store" });
  },

  updateCategory: async (category: string, settings: Record<string, any>): Promise<void> => {
    return apiFetch<void>(`/api/settings/${category}`, {
      method: "PUT",
      body: JSON.stringify(settings),
    });
  },

  // API Keys
  listApiKeys: async (): Promise<ApiKeyOut[]> => {
    const data = await apiFetch<any>("/api/settings/api-keys", { method: "GET" });
    if (Array.isArray(data)) return data.map(normalizeApiKey);
    return (data.items || []).map(normalizeApiKey);
  },

  createApiKey: async (name: string): Promise<ApiKeyCreate> => {
    const data = await apiFetch<any>("/api/settings/api-keys", {
      method: "POST",
      body: JSON.stringify({ name }),
    });
    return { id: data.id, name: data.name, key: data.key };
  },

  revokeApiKey: async (keyId: string): Promise<void> => {
    return apiFetch<void>(`/api/settings/api-keys/${keyId}`, { method: "DELETE" });
  },

  // Sessions
  listSessions: async (): Promise<SessionOut[]> => {
    const data = await apiFetch<any>("/api/settings/sessions", { method: "GET" });
    if (Array.isArray(data)) return data.map(normalizeSession);
    return (data.items || []).map(normalizeSession);
  },

  revokeSession: async (sessionId: string): Promise<void> => {
    return apiFetch<void>(`/api/settings/sessions/${sessionId}`, { method: "DELETE" });
  },

  // Audit log
  getAuditLog: async (limit: number = 5): Promise<AuditLogEntry[]> => {
    const data = await apiFetch<any>(`/api/settings/audit-log?limit=${limit}`, { method: "GET" });
    if (Array.isArray(data)) return data.map(normalizeAuditLog);
    return (data.items || []).map(normalizeAuditLog);
  },
};

function normalizeApiKey(raw: any): ApiKeyOut {
  return {
    id: raw.id,
    name: raw.name,
    prefix: raw.prefix || raw.key_prefix || '',
    lastUsedAt: raw.last_used_at || raw.lastUsedAt || null,
    createdAt: raw.created_at || raw.createdAt || '',
  };
}

function normalizeSession(raw: any): SessionOut {
  return {
    id: raw.id,
    ipAddress: raw.ip_address || raw.ipAddress || null,
    userAgent: raw.user_agent || raw.userAgent || null,
    createdAt: raw.created_at || raw.createdAt || '',
    lastSeenAt: raw.last_seen_at || raw.lastSeenAt || '',
  };
}

function normalizeAuditLog(raw: any): AuditLogEntry {
  return {
    id: raw.id,
    actorUserId: raw.actor_user_id || raw.actorUserId || null,
    action: raw.action,
    target: raw.target || null,
    detail: raw.detail || null,
    createdAt: raw.created_at || raw.createdAt || '',
  };
}
