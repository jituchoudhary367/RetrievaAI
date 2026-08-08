'use client';
// EmbeddingProvidersPanel, SearchProvidersPanel — reuse the same provider card pattern
import React, { useEffect, useState, useCallback } from 'react';
import { workspaceApi, WorkspaceProvider } from '@/lib/api/workspace';
import { EMBEDDING_PROVIDERS, SEARCH_PROVIDERS, getEmbeddingProviderMeta, getSearchProviderMeta } from '@/lib/provider-metadata';
import { Plus, RefreshCw, Database, Search as SearchIcon, AlertTriangle, Info, Wifi, Edit3, Trash2 } from 'lucide-react';
import { ProviderConfigModal } from './ProviderConfigModal';

function StatusDot({ status }: { status: string }) {
  const c: Record<string, string> = {
    connected: 'bg-emerald-400', disconnected: 'bg-[#4a5568]',
    error: 'bg-red-400', validating: 'bg-yellow-400 animate-pulse',
  };
  return <span className={`w-2 h-2 rounded-full inline-block ${c[status] ?? 'bg-[#4a5568]'}`} />;
}

// ── Embedding Dimension Warning ────────────────────────────────────────────────

function DimensionWarning({ configuredDims, currentDims }: { configuredDims?: number; currentDims?: number }) {
  if (!configuredDims || !currentDims || configuredDims === currentDims) return null;
  return (
    <div className="flex items-start gap-2 p-3 rounded-xl bg-yellow-500/5 border border-yellow-500/20 mt-2">
      <AlertTriangle size={13} className="text-yellow-400 shrink-0 mt-0.5" />
      <p className="text-[11px] text-yellow-300 leading-relaxed">
        <strong>Dimension mismatch</strong> — Current Qdrant vectors use {currentDims} dims.
        Switching to {configuredDims} dims will make existing vectors incompatible.
        You must re-index all documents before this provider becomes active.
      </p>
    </div>
  );
}

// ── Generic provider card ──────────────────────────────────────────────────────

function SimpleProviderCard({
  provider, onTest, onEdit, onDelete, onSetDefault, testing, dimensionWarning
}: {
  provider: WorkspaceProvider;
  onTest: () => void;
  onEdit: () => void;
  onDelete: () => void;
  onSetDefault: () => void;
  testing: boolean;
  dimensionWarning?: React.ReactNode;
}) {
  return (
    <div className={`rounded-xl border p-4 transition-all ${
      provider.is_default ? 'border-emerald-500/40 bg-emerald-500/5' : 'border-[#1e2329] bg-[#12181f] hover:border-[#2d3748]'
    }`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <StatusDot status={provider.status} />
          <span className="text-sm font-semibold text-white">{provider.display_name}</span>
          {provider.is_default && (
            <span className="text-[9px] px-1.5 py-0.5 rounded bg-emerald-500/15 text-emerald-400 border border-emerald-500/25 font-bold">DEFAULT</span>
          )}
        </div>
        <div className="flex items-center gap-1.5">
          <button onClick={onSetDefault} className="p-1.5 rounded-lg text-[#4a5568] hover:text-emerald-400 hover:bg-emerald-500/10 transition-colors" title="Set default">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
          </button>
          <button onClick={onEdit} className="p-1.5 rounded-lg text-[#4a5568] hover:text-white hover:bg-white/5 transition-colors" title="Configure"><Edit3 size={12} /></button>
          <button onClick={onDelete} className="p-1.5 rounded-lg text-[#4a5568] hover:text-red-400 hover:bg-red-500/5 transition-colors" title="Remove"><Trash2 size={12} /></button>
        </div>
      </div>
      <div className="flex items-center gap-3 mt-1">
        <span className="text-[10px] text-[#4a5568]">{provider.provider_name}</span>
        {provider.config.model && <span className="text-[10px] text-[#4a5568]">{provider.config.model}</span>}
        {provider.config.dimensions && <span className="text-[10px] text-[#4a5568]">{provider.config.dimensions} dims</span>}
        {provider.latency_ms != null && <span className="text-[10px] text-[#4a5568]">{provider.latency_ms.toFixed(0)}ms</span>}
      </div>
      {provider.last_error && provider.status === 'error' && (
        <p className="mt-2 text-[10px] text-red-400 bg-red-500/5 border border-red-500/15 rounded-lg px-2 py-1.5">{provider.last_error}</p>
      )}
      {dimensionWarning}
      <button onClick={onTest} disabled={testing}
        className="mt-3 flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[11px] font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 hover:bg-emerald-500/20 transition-all disabled:opacity-50">
        {testing ? <RefreshCw size={11} className="animate-spin" /> : <Wifi size={11} />}
        {testing ? 'Testing…' : 'Test Connection'}
      </button>
    </div>
  );
}

function ProviderPanel({
  type, icon: Icon, title, description, allMetas
}: {
  type: 'embedding' | 'search';
  icon: React.ElementType;
  title: string;
  description: string;
  allMetas: any[];
}) {
  const [providers, setProviders] = useState<WorkspaceProvider[]>([]);
  const [loading, setLoading] = useState(true);
  const [testingId, setTestingId] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [editTarget, setEditTarget] = useState<WorkspaceProvider | null>(null);
  const [addingId, setAddingId] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try { setProviders(await workspaceApi.listProviders(type)); } finally { setLoading(false); }
  }, [type]);

  useEffect(() => { load(); }, [load]);

  const handleTest = async (id: string) => {
    setTestingId(id);
    try { await workspaceApi.testProvider(id); await load(); } finally { setTestingId(null); }
  };
  const handleDelete = async (id: string) => {
    if (!confirm('Remove this provider?')) return;
    await workspaceApi.deleteProvider(id); await load();
  };
  const handleSetDefault = async (id: string) => { await workspaceApi.setDefaultProvider(id); await load(); };

  const configuredIds = new Set(providers.map(p => p.provider_name));
  const unconfigured = allMetas.filter((m: any) => !configuredIds.has(m.id));

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-bold text-white">{title}</h2>
          <p className="text-xs text-[#4a5568] mt-0.5">{description}</p>
        </div>
        <button onClick={load} className="p-2 rounded-lg text-[#4a5568] hover:text-white hover:bg-white/5">
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
        </button>
      </div>

      {providers.length > 0 && (
        <div className="space-y-3">
          <p className="text-[11px] font-semibold text-[#4a5568] uppercase tracking-wider">Configured</p>
          {providers.map(p => (
            <SimpleProviderCard
              key={p.id} provider={p}
              testing={testingId === p.id}
              onTest={() => handleTest(p.id)}
              onEdit={() => { setEditTarget(p); setModalOpen(true); }}
              onDelete={() => handleDelete(p.id)}
              onSetDefault={() => handleSetDefault(p.id)}
              dimensionWarning={type === 'embedding' && p.config.dimensions !== undefined ? (
                <DimensionWarning
                  configuredDims={p.config.dimensions}
                  currentDims={undefined /* would come from Qdrant health */}
                />
              ) : undefined}
            />
          ))}
        </div>
      )}

      {/* Info banner for embedding */}
      {type === 'embedding' && (
        <div className="flex items-start gap-2 p-3 rounded-xl bg-[#12181f] border border-[#1e2329]">
          <Info size={13} className="text-emerald-400 shrink-0 mt-0.5" />
          <p className="text-[11px] text-[#6b7280] leading-relaxed">
            Currently using <strong className="text-white">Cohere (system default)</strong>. Adding a provider here overrides it for your workspace only.
            Changing the embedding model requires re-indexing all documents.
          </p>
        </div>
      )}

      {unconfigured.length > 0 && (
        <div className="space-y-2">
          <p className="text-[11px] font-semibold text-[#4a5568] uppercase tracking-wider">Add Provider</p>
          <div className="grid grid-cols-2 gap-2">
            {unconfigured.map((meta: any) => (
              <button key={meta.id}
                onClick={() => { setEditTarget(null); setAddingId(meta.id); setModalOpen(true); }}
                className="flex items-center gap-3 p-3 rounded-xl border border-[#1e2329] bg-[#12181f] hover:border-emerald-500/30 hover:bg-emerald-500/5 transition-all text-left group">
                <div className="w-8 h-8 rounded-lg overflow-hidden shrink-0 flex items-center justify-center p-1" style={{ background: `${meta.color}22` }}>
                  {meta.logo}
                </div>
                <div className="min-w-0">
                  <p className="text-xs font-semibold text-white truncate">{meta.name}</p>
                  {meta.isLocal && <span className="text-[9px] text-yellow-400">Local</span>}
                  {meta.isFree && <span className="text-[9px] text-emerald-400">Free</span>}
                </div>
                <Plus size={12} className="ml-auto text-[#4a5568] group-hover:text-emerald-400 shrink-0" />
              </button>
            ))}
          </div>
        </div>
      )}

      {providers.length === 0 && !loading && (
        <div className="text-center py-10 border border-dashed border-[#1e2329] rounded-xl">
          <Icon size={28} className="mx-auto text-[#4a5568] mb-2" />
          <p className="text-sm text-[#6b7280]">No {title.toLowerCase()} configured</p>
          <p className="text-xs text-[#4a5568] mt-1">System default is used. Add a provider to override.</p>
        </div>
      )}

      {modalOpen && (
        <ProviderConfigModal
          providerType={type}
          existingProvider={editTarget}
          initialProviderId={addingId}
          onClose={() => { setModalOpen(false); setEditTarget(null); setAddingId(null); }}
          onSaved={() => { setModalOpen(false); setEditTarget(null); setAddingId(null); load(); }}
        />
      )}
    </div>
  );
}

// ── Exported panels ────────────────────────────────────────────────────────────

export function EmbeddingProvidersPanel() {
  return (
    <ProviderPanel
      type="embedding"
      icon={Database}
      title="Embedding Providers"
      description="Configure the embedding model for your workspace. Changing provider requires re-indexing all documents."
      allMetas={EMBEDDING_PROVIDERS}
    />
  );
}

export function SearchProvidersPanel() {
  return (
    <ProviderPanel
      type="search"
      icon={SearchIcon}
      title="Search Providers"
      description="Provider for real-time web search during CRAG correction. DuckDuckGo is the default (no key needed)."
      allMetas={SEARCH_PROVIDERS}
    />
  );
}
