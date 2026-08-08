"use client";

/**
 * components/connectors/ConnectorsPanel.tsx
 *
 * Full Google Drive connector management UI.
 * Embedded inside the Settings page as a dedicated panel.
 *
 * Features:
 *   - Connect Google Drive via OAuth
 *   - View connection status, last sync, file counts
 *   - Trigger Full / Incremental sync
 *   - View synced files with status
 *   - Disconnect connector
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  SiGoogledrive, 
  SiNotion, 
  SiConfluence, 
  SiGithub, 
  SiDropbox, 
  SiGooglecloud
} from 'react-icons/si';
import { TbBrandOnedrive, TbBrandAzure } from 'react-icons/tb';
import { FaDatabase, FaFolderOpen, FaAws, FaMicrosoft, FaSlack } from 'react-icons/fa';
import {
  Cloud,
  RefreshCw,
  Trash2,
  FileText,
  CheckCircle2,
  XCircle,
  Clock,
  Loader2,
  HardDrive,
  ChevronDown,
  ChevronRight,
  ExternalLink,
  AlertCircle,
  Zap,
  FolderOpen,
} from 'lucide-react';

import {
  ConnectorOut,
  ConnectorFileOut,
  SyncStatusOut,
  listConnectors,
  getGoogleDriveAuthUrl,
  disconnectConnector,
  triggerSync,
  getSyncStatus,
  getConnectorFiles,
  getConnectorSchemas,
  connectDirectConnector,
  ConnectorProvider,
} from '@/lib/api/connectors';

// ── Helpers ───────────────────────────────────────────────────────────────────

function formatDate(iso: string | null): string {
  if (!iso) return '—';
  return new Date(iso).toLocaleString(undefined, {
    month: 'short', day: 'numeric',
    hour: '2-digit', minute: '2-digit',
  });
}

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, { color: string; label: string }> = {
    connected: { color: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30', label: 'Connected' },
    syncing: { color: 'bg-blue-500/15 text-blue-400 border-blue-500/30', label: 'Syncing…' },
    error: { color: 'bg-red-500/15 text-red-400 border-red-500/30', label: 'Error' },
    disconnected: { color: 'bg-gray-500/15 text-gray-400 border-gray-500/30', label: 'Disconnected' },
    pending_auth: { color: 'bg-amber-500/15 text-amber-400 border-amber-500/30', label: 'Pending Auth' },
    indexed: { color: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30', label: 'Indexed' },
    failed: { color: 'bg-red-500/15 text-red-400 border-red-500/30', label: 'Failed' },
    pending: { color: 'bg-amber-500/15 text-amber-400 border-amber-500/30', label: 'Pending' },
    deleted: { color: 'bg-gray-500/15 text-gray-400 border-gray-500/30', label: 'Deleted' },
  };
  const cfg = map[status] ?? { color: 'bg-gray-500/15 text-gray-400 border-gray-500/30', label: status };
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full border text-[10px] font-medium ${cfg.color}`}>
      {status === 'syncing' && <Loader2 className="w-2.5 h-2.5 animate-spin" />}
      {status === 'connected' && <CheckCircle2 className="w-2.5 h-2.5" />}
      {status === 'error' && <XCircle className="w-2.5 h-2.5" />}
      {cfg.label}
    </span>
  );
}

// ── File List Sub-Component ────────────────────────────────────────────────────

function ConnectorFileList({ connectorId }: { connectorId: string }) {
  const [files, setFiles] = useState<ConnectorFileOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string | undefined>(undefined);

  useEffect(() => {
    getConnectorFiles(connectorId, 1, 50, filter)
      .then(setFiles)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [connectorId, filter]);

  const tabs = [
    { label: 'All', value: undefined },
    { label: 'Indexed', value: 'indexed' },
    { label: 'Failed', value: 'failed' },
    { label: 'Pending', value: 'pending' },
  ];

  return (
    <div className="mt-3 space-y-2">
      {/* Filter tabs */}
      <div className="flex gap-1">
        {tabs.map(t => (
          <button
            key={t.label}
            onClick={() => { setFilter(t.value); setLoading(true); }}
            className={`px-2 py-0.5 rounded text-[10px] font-medium transition-colors ${
              filter === t.value
                ? 'bg-[#1e88e5]/20 text-[#1e88e5] border border-[#1e88e5]/40'
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-4">
          <Loader2 className="w-4 h-4 animate-spin text-muted-foreground" />
        </div>
      ) : files.length === 0 ? (
        <p className="text-[10px] text-muted-foreground text-center py-3">No files found</p>
      ) : (
        <div className="space-y-1 max-h-48 overflow-y-auto pr-1">
          {files.map(f => (
            <div
              key={f.id}
              className="flex items-center justify-between p-2 rounded-lg bg-[#0d1117] border border-[#1e2329] hover:border-[#30363d] transition-colors"
            >
              <div className="flex items-center gap-2 min-w-0">
                <FileText className="w-3 h-3 text-muted-foreground flex-shrink-0" />
                <div className="min-w-0">
                  <p className="text-[10px] text-foreground truncate">
                    {f.remote_file_name || f.remote_file_id}
                  </p>
                  <p className="text-[9px] text-muted-foreground">
                    {formatDate(f.last_synced_at)}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2 flex-shrink-0">
                <StatusBadge status={f.sync_status} />
                {f.remote_url && (
                  <a href={f.remote_url} target="_blank" rel="noopener noreferrer">
                    <ExternalLink className="w-3 h-3 text-muted-foreground hover:text-foreground" />
                  </a>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Icons Helper ─────────────────────────────────────────────────────────────
function getConnectorIcon(provider: string, className: string = "w-4 h-4") {
  switch (provider) {
    case 'google_drive': return <SiGoogledrive className={`${className} text-[#1FA463]`} />;
    case 's3': return <FaAws className={`${className} text-[#FF9900]`} />;
    case 'notion': return <SiNotion className={`${className} text-black dark:text-white`} />;
    case 'confluence': return <SiConfluence className={`${className} text-[#172B4D]`} />;
    case 'slack': return <FaSlack className={`${className} text-[#E01E5A]`} />;
    case 'github': return <SiGithub className={`${className} text-black dark:text-white`} />;
    case 'dropbox': return <SiDropbox className={`${className} text-[#0061FF]`} />;
    case 'sharepoint': return <FaMicrosoft className={`${className} text-[#0078D4]`} />;
    case 'onedrive': return <TbBrandOnedrive className={`${className} text-[#0078D4]`} />;
    case 'gcs': return <SiGooglecloud className={`${className} text-[#4285F4]`} />;
    case 'azure_blob': return <TbBrandAzure className={`${className} text-[#0089D6]`} />;
    case 'database': return <FaDatabase className={`${className} text-[#336791]`} />;
    case 'filesystem': return <FaFolderOpen className={`${className} text-[#F8D775]`} />;
    default: return <Cloud className={`${className} text-muted-foreground`} />;
  }
}

// ── Connector Card ─────────────────────────────────────────────────────────────

function ConnectorCard({
  connector,
  onSync,
  onDisconnect,
  onRefresh,
}: {
  connector: ConnectorOut;
  onSync: (id: string, mode: 'full' | 'incremental') => Promise<void>;
  onDisconnect: (id: string) => Promise<void>;
  onRefresh: () => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);
  const [isDisconnecting, setIsDisconnecting] = useState(false);
  const [syncMode, setSyncMode] = useState<'full' | 'incremental'>('incremental');

  const handleSync = async () => {
    setIsSyncing(true);
    await onSync(connector.id, syncMode);
    setTimeout(() => { setIsSyncing(false); onRefresh(); }, 2000);
  };

  const handleDisconnect = async () => {
    if (!confirm(`Disconnect ${connector.display_name ?? connector.provider}? Indexed documents will remain searchable.`)) return;
    setIsDisconnecting(true);
    await onDisconnect(connector.id);
    onRefresh();
  };

  const isGoogleDrive = connector.provider === 'google_drive';

  return (
    <div className={`rounded-xl border transition-all ${
      connector.status === 'error'
        ? 'border-red-500/30 bg-red-500/5'
        : 'border-[#1e2329] bg-[#12181f]'
    }`}>
      {/* Header */}
      <div className="p-4">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-3 min-w-0">
            {/* Provider icon */}
            <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-[#1e88e5]/5 to-[#1565c0]/5 border border-[#1e88e5]/10 flex items-center justify-center flex-shrink-0">
              {getConnectorIcon(connector.provider)}
            </div>

            <div className="min-w-0">
              <p className="text-sm font-medium text-foreground">
                {connector.display_name ?? connector.provider}
              </p>
              <div className="flex items-center gap-2 mt-0.5">
                <StatusBadge status={connector.status} />
                {connector.root_folder_name && (
                  <span className="flex items-center gap-1 text-[10px] text-muted-foreground">
                    <FolderOpen className="w-3 h-3" />
                    {connector.root_folder_name}
                  </span>
                )}
              </div>
            </div>
          </div>

          <button
            onClick={() => setExpanded(e => !e)}
            className="text-muted-foreground hover:text-foreground transition-colors flex-shrink-0"
          >
            {expanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
          </button>
        </div>

        {/* Stats row */}
        <div className="grid grid-cols-3 gap-2 mt-3">
          <div className="text-center p-2 rounded-lg bg-[#0d1117] border border-[#1e2329]">
            <p className="text-sm font-semibold text-emerald-400">{connector.files_synced}</p>
            <p className="text-[9px] text-muted-foreground">Indexed</p>
          </div>
          <div className="text-center p-2 rounded-lg bg-[#0d1117] border border-[#1e2329]">
            <p className="text-sm font-semibold text-red-400">{connector.files_failed}</p>
            <p className="text-[9px] text-muted-foreground">Failed</p>
          </div>
          <div className="text-center p-2 rounded-lg bg-[#0d1117] border border-[#1e2329]">
            <p className="text-[9px] text-muted-foreground mt-0.5">Last sync</p>
            <p className="text-[9px] text-foreground">{formatDate(connector.last_sync_at)}</p>
          </div>
        </div>

        {/* Error message */}
        {connector.error_message && (
          <div className="mt-2 p-2 rounded-lg bg-red-500/10 border border-red-500/20 flex items-start gap-2">
            <AlertCircle className="w-3 h-3 text-red-400 flex-shrink-0 mt-0.5" />
            <p className="text-[10px] text-red-400">{connector.error_message}</p>
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center gap-2 mt-3">
          {/* Sync mode picker */}
          <select
            value={syncMode}
            onChange={e => setSyncMode(e.target.value as 'full' | 'incremental')}
            className="text-[10px] bg-[#0d1117] border border-[#1e2329] text-muted-foreground rounded px-1.5 py-1"
          >
            <option value="incremental">Incremental</option>
            <option value="full">Full Sync</option>
          </select>

          <button
            onClick={handleSync}
            disabled={isSyncing || connector.status === 'syncing'}
            className="flex-1 flex items-center justify-center gap-1.5 py-1.5 bg-[#1e88e5]/10 hover:bg-[#1e88e5]/20 border border-[#1e88e5]/30 text-[#1e88e5] text-[11px] font-medium rounded-lg transition-colors disabled:opacity-50"
          >
            {isSyncing || connector.status === 'syncing' ? (
              <Loader2 className="w-3 h-3 animate-spin" />
            ) : (
              <RefreshCw className="w-3 h-3" />
            )}
            {isSyncing ? 'Queuing…' : 'Sync'}
          </button>

          <button
            onClick={handleDisconnect}
            disabled={isDisconnecting}
            className="flex items-center justify-center gap-1 py-1.5 px-3 bg-red-500/10 hover:bg-red-500/20 border border-red-500/20 text-red-400 text-[11px] rounded-lg transition-colors disabled:opacity-50"
          >
            {isDisconnecting ? <Loader2 className="w-3 h-3 animate-spin" /> : <Trash2 className="w-3 h-3" />}
          </button>
        </div>
      </div>

      {/* Expanded file list */}
      {expanded && (
        <div className="px-4 pb-4 border-t border-[#1e2329] pt-3">
          <ConnectorFileList connectorId={connector.id} />
        </div>
      )}
    </div>
  );
}

// ── Connect Button ────────────────────────────────────────────────────────────

function ConnectGoogleDriveButton({ onConnected }: { onConnected: () => void }) {
  const [loading, setLoading] = useState(false);

  const handleConnect = async () => {
    setLoading(true);
    try {
      const { auth_url } = await getGoogleDriveAuthUrl();
      // Open the OAuth flow in the same window
      window.location.href = auth_url;
    } catch (err) {
      console.error('Failed to get auth URL:', err);
      setLoading(false);
    }
  };

  return (
    <button
      onClick={handleConnect}
      disabled={loading}
      className="w-full flex items-center justify-center gap-2 py-2.5 bg-gradient-to-r from-[#1e88e5]/10 to-[#1565c0]/10 hover:from-[#1e88e5]/20 hover:to-[#1565c0]/20 border border-[#1e88e5]/30 text-[#1e88e5] text-xs font-medium rounded-xl transition-all duration-200 disabled:opacity-50"
    >
      {loading ? (
        <Loader2 className="w-4 h-4 animate-spin" />
      ) : (
        <HardDrive className="w-4 h-4" />
      )}
      {loading ? 'Redirecting to Google…' : 'Connect Google Drive'}
    </button>
  );
}

// ── Direct Connect Modal ───────────────────────────────────────────────────────

function DirectConnectModal({
  provider,
  schema,
  onClose,
  onConnected,
}: {
  provider: string;
  schema: ConnectorProvider['schema'];
  onClose: () => void;
  onConnected: () => void;
}) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState<Record<string, any>>({});

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await connectDirectConnector(provider, formData);
      onConnected();
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to connect');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="bg-[#12181f] border border-[#1e2329] rounded-2xl w-full max-w-md shadow-2xl overflow-hidden animate-in zoom-in-95">
        <div className="flex items-center justify-between p-4 border-b border-[#1e2329]">
          <h3 className="text-sm font-semibold text-foreground capitalize">
            Connect {provider.replace('_', ' ')}
          </h3>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground">
            <XCircle className="w-5 h-5" />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="p-4 space-y-4">
          {error && (
            <div className="p-2 rounded bg-red-500/10 border border-red-500/20 text-red-400 text-xs">
              {error}
            </div>
          )}
          {schema.length === 0 ? (
            <p className="text-xs text-muted-foreground">
              No configuration required.
            </p>
          ) : (
            schema.map(field => (
              <div key={field.name}>
                <label className="block text-[11px] font-medium text-muted-foreground mb-1">
                  {field.label} {field.required && <span className="text-red-400">*</span>}
                </label>
                <input
                  type={field.type === 'password' ? 'password' : 'text'}
                  required={field.required}
                  value={formData[field.name] || ''}
                  onChange={e => setFormData({ ...formData, [field.name]: e.target.value })}
                  className="w-full bg-[#0d1117] border border-[#1e2329] text-foreground text-xs rounded-lg px-3 py-2 focus:outline-none focus:border-[#1e88e5] transition-colors"
                />
              </div>
            ))
          )}
          <div className="pt-2 flex gap-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 py-2 bg-[#1e2329] hover:bg-[#30363d] text-foreground text-xs font-medium rounded-lg transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 flex items-center justify-center gap-2 py-2 bg-[#1e88e5] hover:bg-[#1565c0] text-white text-xs font-medium rounded-lg transition-colors disabled:opacity-50"
            >
              {loading && <Loader2 className="w-3 h-3 animate-spin" />}
              Connect
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ── Main Panel ────────────────────────────────────────────────────────────────

export default function ConnectorsPanel() {
  const [connectors, setConnectors] = useState<ConnectorOut[]>([]);
  const [providers, setProviders] = useState<ConnectorProvider[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeModal, setActiveModal] = useState<ConnectorProvider | null>(null);
  const [toast, setToast] = useState<string | null>(null);

  const showToast = (msg: string) => {
    setToast(msg);
    setTimeout(() => setToast(null), 3500);
  };

  const fetchConnectors = useCallback(async () => {
    try {
      const [data, provs] = await Promise.all([
        listConnectors(),
        getConnectorSchemas()
      ]);
      setConnectors(data);
      setProviders(provs);
    } catch (err) {
      console.error('Failed to load connectors:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchConnectors();
    // Poll every 15s when a sync might be running
    const interval = setInterval(fetchConnectors, 15000);
    return () => clearInterval(interval);
  }, [fetchConnectors]);

  // Handle OAuth callback params (e.g. ?connector_status=connected)
  useEffect(() => {
    if (typeof window === 'undefined') return;
    const params = new URLSearchParams(window.location.search);
    const status = params.get('connector_status');
    const error = params.get('connector_error');
    if (status === 'connected') {
      showToast('✅ Google Drive connected successfully!');
      // Clean URL
      window.history.replaceState({}, '', window.location.pathname);
      fetchConnectors();
    } else if (error) {
      showToast(`❌ Connection failed: ${decodeURIComponent(error)}`);
      window.history.replaceState({}, '', window.location.pathname);
    }
  }, [fetchConnectors]);

  const handleSync = async (id: string, mode: 'full' | 'incremental') => {
    try {
      await triggerSync(id, mode);
      showToast(`🔄 ${mode === 'full' ? 'Full' : 'Incremental'} sync queued`);
    } catch (err: any) {
      showToast(`❌ Sync failed: ${err.message}`);
    }
  };

  const handleDisconnect = async (id: string) => {
    try {
      await disconnectConnector(id);
      showToast('✅ Connector disconnected');
    } catch (err: any) {
      showToast(`❌ Disconnect failed: ${err.message}`);
    }
  };

  const hasGoogleDrive = connectors.some(c => c.provider === 'google_drive');

  return (
    <div className="space-y-4">
      {/* Toast */}
      {toast && (
        <div className="fixed bottom-4 right-4 z-50 px-4 py-2.5 bg-[#1e2329] border border-[#30363d] rounded-xl shadow-lg text-xs text-foreground animate-in fade-in slide-in-from-bottom-2">
          {toast}
        </div>
      )}

      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-[#1e88e5]/10 border border-[#1e88e5]/20 flex items-center justify-center">
            <Cloud className="w-3.5 h-3.5 text-[#1e88e5]" />
          </div>
          <div>
            <h3 className="text-xs font-semibold text-foreground">Data Connectors</h3>
            <p className="text-[10px] text-muted-foreground">Sync external sources into your knowledge base</p>
          </div>
        </div>
        <button
          onClick={fetchConnectors}
          className="p-1.5 rounded-lg hover:bg-[#1e2329] transition-colors"
          title="Refresh"
        >
          <RefreshCw className="w-3.5 h-3.5 text-muted-foreground" />
        </button>
      </div>

      {/* How it works banner */}
      <div className="p-3 rounded-xl bg-gradient-to-r from-[#1e88e5]/5 to-[#7c3aed]/5 border border-[#1e88e5]/15">
        <div className="flex items-start gap-2">
          <Zap className="w-3.5 h-3.5 text-[#1e88e5] flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-[10px] text-foreground font-medium">How it works</p>
            <p className="text-[10px] text-muted-foreground mt-0.5 leading-relaxed">
              Connect your Google Drive and files are automatically ingested through the full pipeline
              (OCR → Chunk → Embed → Index). They become instantly searchable via your RAG chat.
              Incremental sync detects only changed files.
            </p>
          </div>
        </div>
      </div>

      {/* Loading state */}
      {loading ? (
        <div className="flex items-center justify-center py-8">
          <Loader2 className="w-5 h-5 animate-spin text-muted-foreground" />
        </div>
      ) : (
        <>
          {/* Connected connectors */}
          {connectors.length > 0 && (
            <div className="space-y-3">
              {connectors.map(c => (
                <ConnectorCard
                  key={c.id}
                  connector={c}
                  onSync={handleSync}
                  onDisconnect={handleDisconnect}
                  onRefresh={fetchConnectors}
                />
              ))}
            </div>
          )}

          {/* Available Connectors */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-6">
            {providers.map(p => {
              const isConnected = connectors.some(c => c.provider === p.provider);
              const isGoogle = p.provider === 'google_drive';
              if (isConnected && isGoogle) return null; // Don't show Google Drive button if connected
              return (
                <div key={p.provider} className="rounded-xl border border-dashed border-[#30363d] p-4 flex flex-col justify-between">
                  <div className="flex items-center gap-3 mb-3">
                    <div className="w-9 h-9 rounded-lg bg-[#1e88e5]/5 border border-[#1e88e5]/10 flex items-center justify-center">
                      {getConnectorIcon(p.provider)}
                    </div>
                    <div>
                      <p className="text-xs font-medium text-foreground capitalize">{p.provider.replace('_', ' ')}</p>
                    </div>
                  </div>
                  {isGoogle ? (
                    <ConnectGoogleDriveButton onConnected={fetchConnectors} />
                  ) : (
                    <button
                      onClick={() => setActiveModal(p)}
                      disabled={isConnected}
                      className="w-full py-2 bg-[#1e88e5]/10 hover:bg-[#1e88e5]/20 border border-[#1e88e5]/30 text-[#1e88e5] text-xs font-medium rounded-lg transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                    >
                      {isConnected ? 'Connected' : 'Connect'}
                    </button>
                  )}
                </div>
              );
            })}
          </div>

          {activeModal && (
            <DirectConnectModal
              provider={activeModal.provider}
              schema={activeModal.schema}
              onClose={() => setActiveModal(null)}
              onConnected={() => {
                showToast(`✅ ${activeModal.provider} connected successfully!`);
                fetchConnectors();
              }}
            />
          )}
        </>
      )}
    </div>
  );
}
