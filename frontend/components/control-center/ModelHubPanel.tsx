'use client';

import React, { useEffect, useState, useCallback, useMemo } from 'react';
import { workspaceApi, WorkspaceModel, WorkspaceProvider } from '@/lib/api/workspace';
import {
  Search, Star, RefreshCw, ChevronRight, Zap, Eye, CheckCircle2,
  Cpu, Filter, SortAsc
} from 'lucide-react';
import { getLLMProviderMeta } from '@/lib/provider-metadata';

function ModelBadge({ label, active }: { label: string; active?: boolean }) {
  return (
    <span className={`text-[9px] px-1.5 py-0.5 rounded font-medium border ${
      active
        ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
        : 'bg-[#12181f] text-[#4a5568] border-[#1e2329]'
    }`}>
      {label}
    </span>
  );
}

function ModelRow({ model, onFavorite, onSetDefault }: {
  model: WorkspaceModel;
  onFavorite: () => void;
  onSetDefault: () => void;
}) {
  const meta = getLLMProviderMeta(model.provider_name);
  return (
    <div className={`flex items-center gap-3 px-4 py-3 rounded-xl border transition-all duration-150 ${
      model.is_default
        ? 'border-emerald-500/30 bg-emerald-500/5'
        : 'border-[#1e2329] bg-[#12181f] hover:border-[#2d3748]'
    }`}>
      {/* Provider dot */}
      <div
        className="w-2 h-2 rounded-full shrink-0"
        style={{ background: meta?.color ?? '#4a5568' }}
      />

      {/* Model info */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs font-semibold text-white truncate">{model.model_name}</span>
          {model.is_default && <ModelBadge label="DEFAULT" active />}
          {model.is_recommended && <ModelBadge label="Recommended" active />}
          {model.supports_reasoning && <ModelBadge label="Reasoning" />}
          {model.supports_vision && <ModelBadge label="Vision" />}
          {model.supports_function_calling && <ModelBadge label="Tools" />}
        </div>
        <div className="flex items-center gap-3 mt-0.5">
          <span className="text-[10px] text-[#4a5568]">{model.provider_name}</span>
          {model.context_window && (
            <span className="text-[10px] text-[#4a5568]">{(model.context_window / 1000).toFixed(0)}K ctx</span>
          )}
          {model.input_cost_per_1m != null && (
            <span className="text-[10px] text-[#4a5568]">${model.input_cost_per_1m.toFixed(2)}/1M in</span>
          )}
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-1 shrink-0">
        <button
          onClick={onFavorite}
          className={`p-1.5 rounded-lg transition-colors ${
            model.is_favorite
              ? 'text-yellow-400 bg-yellow-400/10'
              : 'text-[#4a5568] hover:text-yellow-400 hover:bg-yellow-400/10'
          }`}
          title="Toggle favorite"
        >
          <Star size={12} fill={model.is_favorite ? 'currentColor' : 'none'} />
        </button>
        {!model.is_default && (
          <button
            onClick={onSetDefault}
            className="px-2 py-1 rounded-lg text-[10px] font-medium text-[#4a5568] border border-[#1e2329] hover:text-emerald-400 hover:border-emerald-500/30 transition-all"
          >
            Set default
          </button>
        )}
      </div>
    </div>
  );
}

export function ModelHubPanel() {
  const [providers, setProviders] = useState<WorkspaceProvider[]>([]);
  const [models, setModels] = useState<WorkspaceModel[]>([]);
  const [loading, setLoading] = useState(true);
  const [discovering, setDiscovering] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [filterProvider, setFilterProvider] = useState('all');
  const [showFavoritesOnly, setShowFavoritesOnly] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [p, m] = await Promise.all([workspaceApi.listProviders('llm'), workspaceApi.listModels()]);
      setProviders(p);
      setModels(m);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const discover = async (provider: WorkspaceProvider) => {
    setDiscovering(provider.id);
    try {
      await workspaceApi.discoverModels(provider.id);
      await load();
    } finally {
      setDiscovering(null);
    }
  };

  const handleFavorite = async (modelId: string) => {
    await workspaceApi.toggleFavoriteModel(modelId);
    setModels(ms => ms.map(m => m.id === modelId ? { ...m, is_favorite: !m.is_favorite } : m));
  };

  const handleSetDefault = async (modelId: string) => {
    await workspaceApi.setDefaultModel(modelId);
    await load();
  };

  const filtered = useMemo(() => {
    let out = models;
    if (filterProvider !== 'all') out = out.filter(m => m.provider_name === filterProvider);
    if (search) out = out.filter(m =>
      m.model_name.toLowerCase().includes(search.toLowerCase()) ||
      m.model_id.toLowerCase().includes(search.toLowerCase())
    );
    if (showFavoritesOnly) out = out.filter(m => m.is_favorite);
    // Favorites first, then recommended, then alphabetical
    return out.sort((a, b) => {
      if (a.is_favorite !== b.is_favorite) return a.is_favorite ? -1 : 1;
      if (a.is_default !== b.is_default) return a.is_default ? -1 : 1;
      if (a.is_recommended !== b.is_recommended) return a.is_recommended ? -1 : 1;
      return a.model_name.localeCompare(b.model_name);
    });
  }, [models, filterProvider, search, showFavoritesOnly]);

  const uniqueProviders = [...new Set(models.map(m => m.provider_name))];

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-bold text-white">Model Hub</h2>
          <p className="text-xs text-[#4a5568] mt-0.5">Discover, favorite, and set default models per provider.</p>
        </div>
        <button onClick={load} className="p-2 rounded-lg text-[#4a5568] hover:text-white hover:bg-white/5 transition-colors">
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
        </button>
      </div>

      {/* Discover buttons */}
      {providers.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {providers.map(p => (
            <button
              key={p.id}
              onClick={() => discover(p)}
              disabled={discovering === p.id}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium border border-[#1e2329] text-[#6b7280] hover:text-white hover:border-emerald-500/30 transition-all disabled:opacity-50"
            >
              {discovering === p.id
                ? <RefreshCw size={11} className="animate-spin" />
                : <Zap size={11} />
              }
              Discover {p.display_name} models
            </button>
          ))}
        </div>
      )}

      {/* Filters */}
      {models.length > 0 && (
        <div className="flex items-center gap-3">
          <div className="relative flex-1">
            <Search size={12} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#4a5568]" />
            <input
              type="text"
              placeholder="Search models…"
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="w-full pl-8 pr-3 py-2 rounded-lg bg-[#12181f] border border-[#1e2329] text-xs text-white placeholder:text-[#4a5568] focus:outline-none focus:border-emerald-500/50 transition-colors"
            />
          </div>
          <select
            value={filterProvider}
            onChange={e => setFilterProvider(e.target.value)}
            className="px-2 py-2 rounded-lg bg-[#12181f] border border-[#1e2329] text-xs text-[#8b9499] focus:outline-none cursor-pointer"
          >
            <option value="all">All providers</option>
            {uniqueProviders.map(p => <option key={p} value={p}>{p}</option>)}
          </select>
          <button
            onClick={() => setShowFavoritesOnly(v => !v)}
            className={`p-2 rounded-lg border transition-colors ${
              showFavoritesOnly
                ? 'border-yellow-500/30 bg-yellow-500/10 text-yellow-400'
                : 'border-[#1e2329] text-[#4a5568] hover:text-white'
            }`}
            title="Show favorites only"
          >
            <Star size={13} fill={showFavoritesOnly ? 'currentColor' : 'none'} />
          </button>
        </div>
      )}

      {/* Model list */}
      {filtered.length > 0 ? (
        <div className="space-y-2">
          <p className="text-[11px] text-[#4a5568]">{filtered.length} model{filtered.length !== 1 ? 's' : ''}</p>
          {filtered.map(m => (
            <ModelRow
              key={m.id}
              model={m}
              onFavorite={() => handleFavorite(m.id)}
              onSetDefault={() => handleSetDefault(m.id)}
            />
          ))}
        </div>
      ) : (
        <div className="text-center py-12 border border-dashed border-[#1e2329] rounded-xl">
          <Cpu size={32} className="mx-auto text-[#4a5568] mb-3" />
          {providers.length === 0
            ? <p className="text-sm text-[#6b7280]">Add LLM providers first, then discover models.</p>
            : <p className="text-sm text-[#6b7280]">Click "Discover models" to fetch the model catalog.</p>
          }
        </div>
      )}
    </div>
  );
}
