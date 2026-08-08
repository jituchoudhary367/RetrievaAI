'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { workspaceApi, WorkspaceProvider } from '@/lib/api/workspace';
import { LLM_PROVIDERS, getLLMProviderMeta, CAPABILITY_LABELS } from '@/lib/provider-metadata';
import {
  Plus, RefreshCw, Zap, CheckCircle2, XCircle, AlertCircle,
  ChevronRight, Star, MoreVertical, Trash2, Edit3, ArrowUpDown, Wifi
} from 'lucide-react';
import { ProviderConfigModal } from './ProviderConfigModal';

function StatusDot({ status }: { status: string }) {
  const colors: Record<string, string> = {
    connected: 'bg-emerald-400',
    disconnected: 'bg-[#4a5568]',
    error: 'bg-red-400',
    validating: 'bg-yellow-400 animate-pulse',
  };
  return <span className={`w-2 h-2 rounded-full inline-block ${colors[status] ?? 'bg-[#4a5568]'}`} />;
}

function CapabilityBadge({ cap }: { cap: string }) {
  return (
    <span className="text-[9px] px-1.5 py-0.5 rounded border border-[#1e2329] bg-[#12181f] text-[#6b7280] font-medium">
      {CAPABILITY_LABELS[cap as keyof typeof CAPABILITY_LABELS] ?? cap}
    </span>
  );
}

interface ProviderCardProps {
  provider: WorkspaceProvider;
  onTest: () => void;
  onEdit: () => void;
  onDelete: () => void;
  onSetDefault: () => void;
  testing: boolean;
}

function ProviderCard({ provider, onTest, onEdit, onDelete, onSetDefault, testing }: ProviderCardProps) {
  const meta = getLLMProviderMeta(provider.provider_name);
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <div className={`
      relative rounded-xl border transition-all duration-200 p-4
      ${provider.is_default
        ? 'border-emerald-500/40 bg-emerald-500/5 shadow-[0_0_20px_rgba(16,185,129,0.05)]'
        : 'border-[#1e2329] bg-[#12181f] hover:border-[#2d3748]'
      }
    `}>
      {/* Top row */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          {/* Logo */}
          <div
            className="w-9 h-9 rounded-lg flex items-center justify-center overflow-hidden shrink-0"
            style={{ background: `${meta?.color ?? '#333'}22` }}
          >
            {meta?.logo}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-semibold text-white">{provider.display_name}</span>
              {provider.is_default && (
                <span className="text-[9px] px-1.5 py-0.5 rounded bg-emerald-500/15 text-emerald-400 border border-emerald-500/25 font-bold">
                  DEFAULT
                </span>
              )}
              {provider.is_fallback && (
                <span className="text-[9px] px-1.5 py-0.5 rounded bg-blue-500/15 text-blue-400 border border-blue-500/25 font-bold">
                  FALLBACK
                </span>
              )}
            </div>
            <div className="flex items-center gap-1.5 mt-0.5">
              <StatusDot status={provider.status} />
              <span className="text-[10px] text-[#6b7280] capitalize">{provider.status}</span>
              {provider.latency_ms != null && (
                <span className="text-[10px] text-[#4a5568]">· {provider.latency_ms.toFixed(0)}ms</span>
              )}
            </div>
          </div>
        </div>

        {/* Menu */}
        <div className="relative">
          <button
            onClick={() => setMenuOpen(v => !v)}
            className="p-1.5 rounded-lg text-[#4a5568] hover:text-white hover:bg-white/5 transition-colors"
          >
            <MoreVertical size={14} />
          </button>
          {menuOpen && (
            <div className="absolute right-0 top-8 z-20 w-44 rounded-xl border border-[#1e2329] bg-[#12181f] shadow-2xl py-1">
              <button onClick={() => { onSetDefault(); setMenuOpen(false); }}
                className="w-full flex items-center gap-2 px-3 py-2 text-xs text-[#8b9499] hover:text-white hover:bg-white/5 transition-colors">
                <Star size={12} /> Set as Default
              </button>
              <button onClick={() => { onEdit(); setMenuOpen(false); }}
                className="w-full flex items-center gap-2 px-3 py-2 text-xs text-[#8b9499] hover:text-white hover:bg-white/5 transition-colors">
                <Edit3 size={12} /> Configure
              </button>
              <div className="mx-3 my-1 h-px bg-[#1e2329]" />
              <button onClick={() => { onDelete(); setMenuOpen(false); }}
                className="w-full flex items-center gap-2 px-3 py-2 text-xs text-red-400 hover:bg-red-500/5 transition-colors">
                <Trash2 size={12} /> Remove
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Capabilities */}
      {meta && (
        <div className="mt-3 flex flex-wrap gap-1">
          {meta.capabilities.map(c => <CapabilityBadge key={c} cap={c} />)}
          {meta.isLocalOnly && (
            <span className="text-[9px] px-1.5 py-0.5 rounded border border-yellow-500/30 bg-yellow-500/5 text-yellow-400 font-medium">
              Local Only
            </span>
          )}
        </div>
      )}

      {/* Error message */}
      {provider.last_error && provider.status === 'error' && (
        <p className="mt-2 text-[10px] text-red-400 bg-red-500/5 border border-red-500/15 rounded-lg px-2 py-1.5">
          {provider.last_error}
        </p>
      )}

      {/* Actions */}
      <div className="mt-3 flex items-center gap-2">
        <button
          onClick={onTest}
          disabled={testing}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[11px] font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 hover:bg-emerald-500/20 transition-all disabled:opacity-50"
        >
          {testing ? <RefreshCw size={11} className="animate-spin" /> : <Wifi size={11} />}
          {testing ? 'Testing…' : 'Test Connection'}
        </button>
        <button
          onClick={onEdit}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[11px] font-medium text-[#6b7280] border border-[#1e2329] hover:text-white hover:border-[#2d3748] transition-all"
        >
          <Edit3 size={11} /> Configure
        </button>
      </div>
    </div>
  );
}

export function LLMProvidersPanel() {
  const [providers, setProviders] = useState<WorkspaceProvider[]>([]);
  const [loading, setLoading] = useState(true);
  const [testingId, setTestingId] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [editTarget, setEditTarget] = useState<WorkspaceProvider | null>(null);
  const [addingId, setAddingId] = useState<string | null>(null); // which provider to add

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await workspaceApi.listProviders('llm');
      setProviders(data);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleTest = async (id: string) => {
    setTestingId(id);
    try {
      await workspaceApi.testProvider(id);
      await load();
    } finally {
      setTestingId(null);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Remove this provider?')) return;
    await workspaceApi.deleteProvider(id);
    await load();
  };

  const handleSetDefault = async (id: string) => {
    await workspaceApi.setDefaultProvider(id);
    await load();
  };

  const configuredIds = new Set(providers.map(p => p.provider_name));
  const unconfigured = LLM_PROVIDERS.filter(m => !configuredIds.has(m.id));

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-bold text-white">AI Providers</h2>
          <p className="text-xs text-[#4a5568] mt-0.5">Manage workspace-scoped LLM providers. Falls back to system default if none configured.</p>
        </div>
        <button
          onClick={load}
          className="p-2 rounded-lg text-[#4a5568] hover:text-white hover:bg-white/5 transition-colors"
        >
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
        </button>
      </div>

      {/* Configured providers */}
      {providers.length > 0 && (
        <div className="space-y-3">
          <p className="text-[11px] font-semibold text-[#4a5568] uppercase tracking-wider">Configured</p>
          {providers.map(p => (
            <ProviderCard
              key={p.id}
              provider={p}
              testing={testingId === p.id}
              onTest={() => handleTest(p.id)}
              onEdit={() => { setEditTarget(p); setModalOpen(true); }}
              onDelete={() => handleDelete(p.id)}
              onSetDefault={() => handleSetDefault(p.id)}
            />
          ))}
        </div>
      )}

      {/* Add new providers */}
      {unconfigured.length > 0 && (
        <div className="space-y-2">
          <p className="text-[11px] font-semibold text-[#4a5568] uppercase tracking-wider">Add Provider</p>
          <div className="grid grid-cols-2 gap-2">
            {unconfigured.map(meta => (
              <button
                key={meta.id}
                onClick={() => { setEditTarget(null); setAddingId(meta.id); setModalOpen(true); }}
                className="flex items-center gap-3 p-3 rounded-xl border border-[#1e2329] bg-[#12181f] hover:border-emerald-500/30 hover:bg-emerald-500/5 transition-all text-left group"
              >
                <div
                  className="w-8 h-8 rounded-lg flex items-center justify-center overflow-hidden shrink-0 p-1"
                  style={{ background: `${meta.color}22` }}
                >
                  {meta.logo}
                </div>
                <div className="min-w-0">
                  <p className="text-xs font-semibold text-white truncate">{meta.name}</p>
                  {meta.isLocalOnly && (
                    <span className="text-[9px] text-yellow-400">Local Only</span>
                  )}
                </div>
                <Plus size={12} className="ml-auto text-[#4a5568] group-hover:text-emerald-400 transition-colors shrink-0" />
              </button>
            ))}
          </div>
        </div>
      )}

      {providers.length === 0 && !loading && (
        <div className="text-center py-12 border border-dashed border-[#1e2329] rounded-xl">
          <Zap size={32} className="mx-auto text-[#4a5568] mb-3" />
          <p className="text-sm font-medium text-[#6b7280]">No LLM providers configured</p>
          <p className="text-xs text-[#4a5568] mt-1">The system falls back to Groq (default). Add a provider to override.</p>
        </div>
      )}

      {/* Config Modal */}
      {modalOpen && (
        <ProviderConfigModal
          providerType="llm"
          existingProvider={editTarget}
          initialProviderId={addingId}
          onClose={() => { setModalOpen(false); setEditTarget(null); setAddingId(null); }}
          onSaved={() => { setModalOpen(false); setEditTarget(null); setAddingId(null); load(); }}
        />
      )}
    </div>
  );
}
