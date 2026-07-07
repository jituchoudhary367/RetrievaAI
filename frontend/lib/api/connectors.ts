/**
 * lib/api/connectors.ts
 *
 * TypeScript API client for the connector framework endpoints.
 */

import { apiFetch, apiBaseUrl } from './client';

// ── Types ─────────────────────────────────────────────────────────────────────

export interface ConnectorOut {
  id: string;
  provider: string;
  display_name: string | null;
  status: 'pending_auth' | 'connected' | 'disconnected' | 'syncing' | 'error';
  auto_sync: boolean;
  sync_interval_minutes: number;
  root_folder_name: string | null;
  error_message: string | null;
  created_at: string;
  last_sync_at: string | null;
  files_synced: number;
  files_failed: number;
}

export interface ConnectorFileOut {
  id: string;
  remote_file_id: string;
  remote_file_name: string | null;
  remote_mime_type: string | null;
  sync_status: 'pending' | 'syncing' | 'indexed' | 'failed' | 'deleted';
  sync_error: string | null;
  document_id: string | null;
  last_synced_at: string | null;
  remote_url: string | null;
}

export interface SyncStatusOut {
  connector_id: string;
  status: string;
  last_sync_mode: string | null;
  last_sync_started_at: string | null;
  last_sync_completed_at: string | null;
  last_sync_status: string | null;
  files_discovered: number;
  files_synced: number;
  files_failed: number;
  change_token_set: boolean;
}

export interface AuthUrlResponse {
  auth_url: string;
  state: string;
}

// ── API Functions ─────────────────────────────────────────────────────────────

export async function listConnectors(): Promise<ConnectorOut[]> {
  return apiFetch<ConnectorOut[]>('/api/connectors');
}

export async function getGoogleDriveAuthUrl(): Promise<AuthUrlResponse> {
  return apiFetch<AuthUrlResponse>('/api/connectors/google-drive/auth');
}

export async function disconnectConnector(connectorId: string): Promise<void> {
  return apiFetch<void>(`/api/connectors/${connectorId}`, { method: 'DELETE' });
}

export async function triggerSync(
  connectorId: string,
  mode: 'full' | 'incremental' = 'incremental'
): Promise<{ connector_id: string; mode: string; status: string }> {
  return apiFetch(`/api/connectors/${connectorId}/sync`, {
    method: 'POST',
    body: JSON.stringify({ mode }),
  });
}

export async function getSyncStatus(connectorId: string): Promise<SyncStatusOut> {
  return apiFetch<SyncStatusOut>(`/api/connectors/${connectorId}/status`);
}

export async function getConnectorFiles(
  connectorId: string,
  page = 1,
  pageSize = 50,
  statusFilter?: string
): Promise<ConnectorFileOut[]> {
  const params = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
  });
  if (statusFilter) params.set('status_filter', statusFilter);
  return apiFetch<ConnectorFileOut[]>(`/api/connectors/${connectorId}/files?${params}`);
}

export async function getConnectorAnalytics(): Promise<{
  total_connectors: number;
  connected: number;
  syncing: number;
  connectors: Array<{
    connector_id: string;
    provider: string;
    display_name: string;
    status: string;
    files_indexed: number;
    files_failed: number;
    files_pending: number;
    last_sync_at: string | null;
    last_sync_status: string | null;
  }>;
}> {
  return apiFetch('/api/analytics/connectors');
}
