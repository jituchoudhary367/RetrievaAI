// lib/api/workspace.ts
// TypeScript client for all /api/workspace/* endpoints

import { apiFetch } from './client';

// ── Types ─────────────────────────────────────────────────────────────────────

export type ProviderType = 'llm' | 'embedding' | 'search';
export type ProviderStatus = 'connected' | 'disconnected' | 'error' | 'validating';
export type HealthStatus = 'healthy' | 'degraded' | 'down';

export interface WorkspaceProvider {
  id: string;
  user_id: string;
  provider_type: ProviderType;
  provider_name: string;
  display_name: string;
  config: Record<string, any>;
  is_default: boolean;
  is_fallback: boolean;
  status: ProviderStatus;
  health_status: HealthStatus | null;
  last_validated_at: string | null;
  latency_ms: number | null;
  last_error: string | null;
  created_at: string | null;
}

export interface WorkspaceModel {
  id: string;
  model_id: string;
  model_name: string;
  provider_name: string;
  context_window: number | null;
  input_cost_per_1m: number | null;
  output_cost_per_1m: number | null;
  supports_streaming: boolean;
  supports_vision: boolean;
  supports_json_mode: boolean;
  supports_function_calling: boolean;
  supports_reasoning: boolean;
  is_recommended: boolean;
  is_default: boolean;
  is_favorite: boolean;
  last_fetched_at: string | null;
}

export interface RuntimeConfig {
  chunk_size: number;
  chunk_overlap: number;
  top_k: number;
  rerank_top_n: number;
  hybrid_alpha: number;
  cache_ttl: number;
  memory_window: number;
  streaming_enabled: boolean;
  crag_enabled: boolean;
  web_search_enabled: boolean;
  code_search_enabled: boolean;
  reranking_enabled: boolean;
  semantic_cache_enabled: boolean;
  ocr_enabled: boolean;
  vision_enabled: boolean;
  telemetry_enabled: boolean;
  analytics_enabled: boolean;
  embedding_batch_size: number;
  bm25_weight: number;
  vector_weight: number;
}

export interface TestConnectionResult {
  success: boolean;
  latency_ms: number;
  error?: string;
  model_count?: number;
  dimensions?: number;
  status: ProviderStatus;
  provider_id: string;
}

export interface WorkspaceUsage {
  days: number;
  total_queries: number;
  total_tokens: number;
  avg_latency_ms: number;
  cache_hit_rate: number;
  cache_hits: number;
}

// ── Provider API ──────────────────────────────────────────────────────────────

export const workspaceApi = {
  // Providers
  listProviders: (type?: ProviderType): Promise<WorkspaceProvider[]> =>
    apiFetch(`/workspace/providers${type ? `?provider_type=${type}` : ''}`),

  getProvider: (id: string): Promise<WorkspaceProvider> =>
    apiFetch(`/workspace/providers/${id}`),

  createProvider: (data: {
    provider_type: ProviderType;
    provider_name: string;
    display_name?: string;
    config: Record<string, any>;
  }): Promise<WorkspaceProvider> =>
    apiFetch('/workspace/providers', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  updateProvider: (id: string, data: {
    display_name?: string;
    config: Record<string, any>;
  }): Promise<WorkspaceProvider> =>
    apiFetch(`/workspace/providers/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  deleteProvider: (id: string): Promise<void> =>
    apiFetch(`/workspace/providers/${id}`, { method: 'DELETE' }),

  testProvider: (id: string): Promise<TestConnectionResult> =>
    apiFetch(`/workspace/providers/${id}/test`, { method: 'POST' }),

  setDefaultProvider: (id: string): Promise<{ success: boolean }> =>
    apiFetch(`/workspace/providers/${id}/set-default`, { method: 'POST' }),

  setFallbackProvider: (id: string): Promise<{ success: boolean }> =>
    apiFetch(`/workspace/providers/${id}/set-fallback`, { method: 'POST' }),

  // Models
  listModels: (providerName?: string): Promise<WorkspaceModel[]> =>
    apiFetch(`/workspace/models${providerName ? `?provider_name=${providerName}` : ''}`),

  discoverModels: (providerId: string): Promise<WorkspaceModel[]> =>
    apiFetch(`/workspace/models/discover/${providerId}`, { method: 'POST' }),

  toggleFavoriteModel: (modelId: string): Promise<{ success: boolean }> =>
    apiFetch(`/workspace/models/${modelId}/favorite`, { method: 'POST' }),

  setDefaultModel: (modelId: string): Promise<{ success: boolean }> =>
    apiFetch(`/workspace/models/${modelId}/set-default`, { method: 'POST' }),

  // Runtime Config
  getRuntimeConfig: (): Promise<RuntimeConfig> =>
    apiFetch('/workspace/runtime'),

  updateRuntimeConfig: (updates: Partial<RuntimeConfig>): Promise<RuntimeConfig> =>
    apiFetch('/workspace/runtime', {
      method: 'PUT',
      body: JSON.stringify({ updates }),
    }),

  updateRuntimeKey: (key: string, value: any): Promise<{ key: string; value: any; success: boolean }> =>
    apiFetch(`/workspace/runtime/${key}`, {
      method: 'PUT',
      body: JSON.stringify({ value }),
    }),

  // Health & Usage
  getHealth: (): Promise<Record<string, any>> =>
    apiFetch('/workspace/health'),

  getUsage: (days = 7): Promise<WorkspaceUsage> =>
    apiFetch(`/workspace/usage?days=${days}`),
};
