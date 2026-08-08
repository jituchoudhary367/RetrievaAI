'use client';

import React, { useEffect, useState } from 'react';
import { workspaceApi, WorkspaceProvider, ProviderType } from '@/lib/api/workspace';
import { LLM_PROVIDERS, EMBEDDING_PROVIDERS, SEARCH_PROVIDERS, getLLMProviderMeta, getEmbeddingProviderMeta, getSearchProviderMeta, ProviderField } from '@/lib/provider-metadata';
import { X, Eye, EyeOff, Loader2, CheckCircle2, AlertCircle, Info } from 'lucide-react';

interface Props {
  providerType: ProviderType;
  existingProvider?: WorkspaceProvider | null;
  initialProviderId?: string | null;
  onClose: () => void;
  onSaved: () => void;
}

function getMeta(type: ProviderType, id: string) {
  if (type === 'llm') return getLLMProviderMeta(id);
  if (type === 'embedding') return getEmbeddingProviderMeta(id);
  if (type === 'search') return getSearchProviderMeta(id);
  return undefined;
}

function getProviderList(type: ProviderType) {
  if (type === 'llm') return LLM_PROVIDERS;
  if (type === 'embedding') return EMBEDDING_PROVIDERS;
  return SEARCH_PROVIDERS;
}

function InputField({ field, value, onChange }: { field: ProviderField; value: any; onChange: (v: any) => void }) {
  const [show, setShow] = useState(false);
  const baseInput = 'w-full bg-[#0d1117] border border-[#1e2329] rounded-lg px-3 py-2 text-xs text-white placeholder:text-[#4a5568] focus:outline-none focus:border-emerald-500/50 transition-colors';

  if (field.type === 'toggle') {
    return (
      <div className="flex items-center justify-between">
        <span className="text-xs text-[#8b9499]">{field.label}</span>
        <button
          type="button"
          onClick={() => onChange(!value)}
          className={`relative w-10 h-5 rounded-full transition-colors ${value ? 'bg-emerald-500' : 'bg-[#1e2329]'}`}
        >
          <span className={`absolute top-0.5 w-4 h-4 rounded-full bg-white transition-transform ${value ? 'translate-x-5' : 'translate-x-0.5'}`} />
        </button>
      </div>
    );
  }

  if (field.type === 'select') {
    return (
      <div>
        <label className="block text-[10px] text-[#4a5568] mb-1">{field.label}</label>
        <select
          className={baseInput + ' cursor-pointer'}
          value={value ?? ''}
          onChange={e => onChange(e.target.value)}
        >
          {field.options?.map(o => <option key={o} value={o}>{o}</option>)}
        </select>
      </div>
    );
  }

  if (field.type === 'password') {
    return (
      <div>
        <label className="block text-[10px] text-[#4a5568] mb-1">
          {field.label} {field.required && <span className="text-red-400">*</span>}
        </label>
        <div className="relative">
          <input
            type={show ? 'text' : 'password'}
            className={baseInput + ' pr-9'}
            placeholder={field.placeholder}
            value={value ?? ''}
            onChange={e => onChange(e.target.value)}
          />
          <button
            type="button"
            onClick={() => setShow(v => !v)}
            className="absolute right-2 top-1/2 -translate-y-1/2 text-[#4a5568] hover:text-white"
          >
            {show ? <EyeOff size={13} /> : <Eye size={13} />}
          </button>
        </div>
        {value && value.length > 4 && (
          <p className="text-[10px] text-emerald-500 mt-1 flex items-center gap-1">
            <CheckCircle2 size={10} /> Key will be encrypted at rest
          </p>
        )}
      </div>
    );
  }

  if (field.type === 'number') {
    return (
      <div>
        <label className="block text-[10px] text-[#4a5568] mb-1">{field.label}</label>
        <input
          type="number"
          className={baseInput}
          min={field.min}
          max={field.max}
          step={field.step ?? 1}
          value={value ?? ''}
          onChange={e => onChange(field.step ? parseFloat(e.target.value) : parseInt(e.target.value))}
        />
      </div>
    );
  }

  return (
    <div>
      <label className="block text-[10px] text-[#4a5568] mb-1">
        {field.label} {field.required && <span className="text-red-400">*</span>}
      </label>
      <input
        type={field.type}
        className={baseInput}
        placeholder={field.placeholder}
        value={value ?? ''}
        onChange={e => onChange(e.target.value)}
      />
    </div>
  );
}

export function ProviderConfigModal({ providerType, existingProvider, initialProviderId, onClose, onSaved }: Props) {
  const allProviders = getProviderList(providerType);
  const defaultId = existingProvider?.provider_name ?? initialProviderId ?? allProviders[0]?.id;

  const [selectedId, setSelectedId] = useState(defaultId ?? '');
  const [displayName, setDisplayName] = useState(existingProvider?.display_name ?? '');
  const [config, setConfig] = useState<Record<string, any>>(existingProvider?.config ?? {});
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; error?: string; latency_ms?: number } | null>(null);
  const [error, setError] = useState('');

  const meta = getMeta(providerType, selectedId);
  const fields = (meta as any)?.fields ?? [];

  const updateConfig = (key: string, val: any) => setConfig(c => ({ ...c, [key]: val }));

  const handleSave = async () => {
    setSaving(true);
    setError('');
    try {
      if (existingProvider) {
        await workspaceApi.updateProvider(existingProvider.id, { display_name: displayName, config });
      } else {
        await workspaceApi.createProvider({
          provider_type: providerType,
          provider_name: selectedId,
          display_name: displayName || undefined,
          config,
        });
      }
      onSaved();
    } catch (e: any) {
      setError(e.message ?? 'Failed to save provider');
    } finally {
      setSaving(false);
    }
  };

  const handleTest = async () => {
    if (!existingProvider) {
      setTestResult({ success: false, error: 'Save the provider first, then test connection.' });
      return;
    }
    setTesting(true);
    setTestResult(null);
    try {
      const result = await workspaceApi.testProvider(existingProvider.id);
      setTestResult(result);
    } finally {
      setTesting(false);
    }
  };

  const typeLabel = providerType === 'llm' ? 'LLM' : providerType === 'embedding' ? 'Embedding' : 'Search';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm">
      <div className="w-full max-w-lg bg-[#0d1117] border border-[#1e2329] rounded-2xl shadow-2xl flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-[#1e2329]">
          <div>
            <h3 className="text-sm font-bold text-white">
              {existingProvider ? `Configure ${existingProvider.display_name}` : `Add ${typeLabel} Provider`}
            </h3>
            <p className="text-[10px] text-[#4a5568] mt-0.5">API keys are encrypted with AES-256-GCM before storage</p>
          </div>
          <button onClick={onClose} className="p-1.5 text-[#4a5568] hover:text-white rounded-lg hover:bg-white/5 transition-colors">
            <X size={16} />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto px-5 py-4 space-y-4">
          {/* Provider selector (only when adding new) */}
          {!existingProvider && (
            <div>
              <label className="block text-[10px] text-[#4a5568] mb-2">Provider</label>
              <div className="grid grid-cols-2 gap-2">
                {allProviders.map((p: any) => (
                  <button
                    key={p.id}
                    type="button"
                    onClick={() => { setSelectedId(p.id); setConfig({}); }}
                    className={`flex items-center gap-2 p-2.5 rounded-xl border text-left transition-all ${
                      selectedId === p.id
                        ? 'border-emerald-500/40 bg-emerald-500/5 text-white'
                        : 'border-[#1e2329] text-[#6b7280] hover:border-[#2d3748] hover:text-white'
                    }`}
                  >
                    <div
                      className="w-7 h-7 rounded-lg shrink-0 overflow-hidden flex items-center justify-center p-1"
                      style={{ background: `${p.color}22` }}
                    >
                      {p.logo}
                    </div>
                    <span className="text-xs font-medium truncate">{p.name}</span>
                    {p.isLocalOnly && <span className="text-[9px] text-yellow-400 ml-auto shrink-0">Local</span>}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Display name */}
          <div>
            <label className="block text-[10px] text-[#4a5568] mb-1">Display Name (optional)</label>
            <input
              type="text"
              className="w-full bg-[#0d1117] border border-[#1e2329] rounded-lg px-3 py-2 text-xs text-white placeholder:text-[#4a5568] focus:outline-none focus:border-emerald-500/50 transition-colors"
              placeholder={`My ${meta?.name ?? 'Provider'}`}
              value={displayName}
              onChange={e => setDisplayName(e.target.value)}
            />
          </div>

          {/* Ollama local-only notice */}
          {(meta as any)?.isLocalOnly && (
            <div className="flex items-start gap-2 p-3 rounded-xl bg-yellow-500/5 border border-yellow-500/20">
              <Info size={13} className="text-yellow-400 shrink-0 mt-0.5" />
              <p className="text-[11px] text-yellow-300 leading-relaxed">
                <strong>Local Only</strong> — Ollama must be running on the same machine or a reachable server.
                This provider is not available in cloud deployments (e.g., Render).
              </p>
            </div>
          )}

          {/* Dynamic fields */}
          {fields.map((field: ProviderField) => (
            <InputField
              key={field.key}
              field={field}
              value={config[field.key]}
              onChange={val => updateConfig(field.key, val)}
            />
          ))}

          {/* Test result */}
          {testResult && (
            <div className={`flex items-start gap-2 p-3 rounded-xl border ${
              testResult.success
                ? 'bg-emerald-500/5 border-emerald-500/20 text-emerald-400'
                : 'bg-red-500/5 border-red-500/20 text-red-400'
            }`}>
              {testResult.success
                ? <CheckCircle2 size={13} className="shrink-0 mt-0.5" />
                : <AlertCircle size={13} className="shrink-0 mt-0.5" />
              }
              <p className="text-[11px] leading-relaxed">
                {testResult.success
                  ? `Connection successful · ${testResult.latency_ms?.toFixed(0)}ms`
                  : testResult.error}
              </p>
            </div>
          )}

          {error && (
            <p className="text-[11px] text-red-400 bg-red-500/5 border border-red-500/20 rounded-lg px-3 py-2">
              {error}
            </p>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-5 py-4 border-t border-[#1e2329]">
          <button
            type="button"
            onClick={handleTest}
            disabled={testing}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium text-[#6b7280] border border-[#1e2329] hover:text-white hover:border-[#2d3748] transition-all disabled:opacity-50"
          >
            {testing ? <Loader2 size={12} className="animate-spin" /> : null}
            Test Connection
          </button>
          <div className="flex items-center gap-2">
            <button onClick={onClose} className="px-4 py-2 rounded-lg text-xs text-[#6b7280] hover:text-white transition-colors">
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={saving}
              className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-semibold bg-emerald-500 text-black hover:bg-emerald-400 transition-all disabled:opacity-50"
            >
              {saving ? <Loader2 size={12} className="animate-spin" /> : null}
              {existingProvider ? 'Save Changes' : 'Add Provider'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
