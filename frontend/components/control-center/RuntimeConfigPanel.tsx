'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { workspaceApi, RuntimeConfig } from '@/lib/api/workspace';
import { Sliders, RefreshCw, Save, RotateCcw, Info } from 'lucide-react';

// ── Slider ─────────────────────────────────────────────────────────────────────

function ConfigSlider({
  label, description, value, min, max, step = 1, unit = '', onChange
}: {
  label: string; description?: string; value: number; min: number; max: number;
  step?: number; unit?: string; onChange: (v: number) => void;
}) {
  const pct = ((value - min) / (max - min)) * 100;
  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between">
        <div>
          <span className="text-xs font-medium text-white">{label}</span>
          {description && <p className="text-[10px] text-[#4a5568] mt-0.5">{description}</p>}
        </div>
        <span className="text-xs font-mono font-bold text-emerald-400 min-w-[60px] text-right">
          {value}{unit}
        </span>
      </div>
      <div className="relative h-5 flex items-center">
        <div className="absolute inset-x-0 h-1 rounded-full bg-[#1e2329]" />
        <div
          className="absolute left-0 h-1 rounded-full bg-emerald-500"
          style={{ width: `${pct}%` }}
        />
        <input
          type="range" min={min} max={max} step={step} value={value}
          onChange={e => onChange(step < 1 ? parseFloat(e.target.value) : parseInt(e.target.value))}
          className="absolute inset-0 w-full opacity-0 cursor-pointer h-5"
        />
        <div
          className="absolute w-3.5 h-3.5 rounded-full bg-emerald-400 border-2 border-[#0d1117] shadow-lg pointer-events-none"
          style={{ left: `calc(${pct}% - 7px)` }}
        />
      </div>
      <div className="flex justify-between text-[9px] text-[#4a5568]">
        <span>{min}{unit}</span><span>{max}{unit}</span>
      </div>
    </div>
  );
}

// ── Toggle ─────────────────────────────────────────────────────────────────────

function ConfigToggle({
  label, description, value, onChange
}: {
  label: string; description?: string; value: boolean; onChange: (v: boolean) => void;
}) {
  return (
    <div className="flex items-start justify-between gap-4 py-2">
      <div>
        <p className="text-xs font-medium text-white">{label}</p>
        {description && <p className="text-[10px] text-[#4a5568] mt-0.5">{description}</p>}
      </div>
      <button
        type="button"
        onClick={() => onChange(!value)}
        className={`relative w-10 h-5 rounded-full transition-colors shrink-0 mt-0.5 ${value ? 'bg-emerald-500' : 'bg-[#1e2329]'}`}
      >
        <span className={`absolute top-0.5 w-4 h-4 rounded-full bg-white transition-all duration-200 ${value ? 'translate-x-5' : 'translate-x-0.5'}`} />
      </button>
    </div>
  );
}

// ── Section ────────────────────────────────────────────────────────────────────

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-[#1e2329] bg-[#12181f] p-4 space-y-4">
      <h3 className="text-[11px] font-bold text-[#4a5568] uppercase tracking-wider">{title}</h3>
      {children}
    </div>
  );
}

// ── Main Panel ─────────────────────────────────────────────────────────────────

export function RuntimeConfigPanel() {
  const [config, setConfig] = useState<RuntimeConfig | null>(null);
  const [original, setOriginal] = useState<RuntimeConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const c = await workspaceApi.getRuntimeConfig();
      setConfig(c); setOriginal(c);
    } finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const update = (key: keyof RuntimeConfig, value: any) => {
    setConfig(c => c ? { ...c, [key]: value } : c);
    setSaved(false);
  };

  const handleSave = async () => {
    if (!config) return;
    setSaving(true);
    try {
      const updated = await workspaceApi.updateRuntimeConfig(config);
      setConfig(updated); setOriginal(updated);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } finally { setSaving(false); }
  };

  const handleReset = () => { setConfig(original); setSaved(false); };

  const isDirty = JSON.stringify(config) !== JSON.stringify(original);

  if (loading || !config) {
    return (
      <div className="flex items-center justify-center py-20">
        <RefreshCw size={20} className="animate-spin text-emerald-400" />
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-bold text-white">Runtime Configuration</h2>
          <p className="text-xs text-[#4a5568] mt-0.5">
            Tune pipeline parameters. Changes take effect immediately — no restart required.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {isDirty && (
            <button onClick={handleReset}
              className="p-2 rounded-lg text-[#4a5568] hover:text-white hover:bg-white/5 transition-colors">
              <RotateCcw size={14} />
            </button>
          )}
          <button
            onClick={handleSave}
            disabled={saving || !isDirty}
            className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-semibold transition-all ${
              isDirty
                ? 'bg-emerald-500 text-black hover:bg-emerald-400'
                : saved
                  ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                  : 'bg-[#1e2329] text-[#4a5568] cursor-not-allowed'
            }`}
          >
            <Save size={12} />
            {saving ? 'Saving…' : saved ? 'Saved ✓' : 'Save Changes'}
          </button>
        </div>
      </div>

      {/* Retrieval */}
      <Section title="Retrieval">
        <ConfigSlider
          label="Top-K Results" description="Documents retrieved per sub-query"
          value={config.top_k} min={1} max={50}
          onChange={v => update('top_k', v)}
        />
        <ConfigSlider
          label="Rerank Top-N" description="Documents sent to LLM after reranking"
          value={config.rerank_top_n} min={1} max={20}
          onChange={v => update('rerank_top_n', v)}
        />
        <ConfigSlider
          label="Hybrid Alpha (Vector vs BM25)" description="0 = BM25 only · 1 = Vector only"
          value={config.hybrid_alpha} min={0} max={1} step={0.05}
          onChange={v => update('hybrid_alpha', v)}
        />
      </Section>

      {/* Chunking */}
      <Section title="Chunking">
        <ConfigSlider
          label="Chunk Size" description="Characters per chunk during ingestion"
          value={config.chunk_size} min={128} max={4096} step={128}
          onChange={v => update('chunk_size', v)}
        />
        <ConfigSlider
          label="Chunk Overlap" description="Overlap between consecutive chunks"
          value={config.chunk_overlap} min={0} max={512} step={32}
          onChange={v => update('chunk_overlap', v)}
        />
        <ConfigSlider
          label="Embedding Batch Size" description="Chunks embedded per API call"
          value={config.embedding_batch_size} min={1} max={256} step={8}
          onChange={v => update('embedding_batch_size', v)}
        />
      </Section>

      {/* Memory & Cache */}
      <Section title="Memory & Cache">
        <ConfigSlider
          label="Conversation Memory Window" description="Message turns kept in context"
          value={config.memory_window} min={1} max={50}
          onChange={v => update('memory_window', v)}
        />
        <ConfigSlider
          label="Semantic Cache TTL" description="Seconds before cached answers expire"
          value={config.cache_ttl} min={60} max={86400} step={60} unit="s"
          onChange={v => update('cache_ttl', v)}
        />
      </Section>

      {/* Feature Flags */}
      <Section title="Feature Flags">
        <ConfigToggle
          label="Streaming Responses"
          description="Stream LLM tokens to the UI in real-time"
          value={config.streaming_enabled}
          onChange={v => update('streaming_enabled', v)}
        />
        <div className="h-px bg-[#1e2329]" />
        <ConfigToggle
          label="CRAG (Corrective RAG)"
          description="Grade retrieved documents and fall back to web search if insufficient"
          value={config.crag_enabled}
          onChange={v => update('crag_enabled', v)}
        />
        <div className="h-px bg-[#1e2329]" />
        <ConfigToggle
          label="Web Search Tool"
          description="Allow the assistant to search the web during query"
          value={config.web_search_enabled}
          onChange={v => update('web_search_enabled', v)}
        />
        <div className="h-px bg-[#1e2329]" />
        <ConfigToggle
          label="Reranking"
          description="Use cross-encoder reranking for better result quality"
          value={config.reranking_enabled}
          onChange={v => update('reranking_enabled', v)}
        />
        <div className="h-px bg-[#1e2329]" />
        <ConfigToggle
          label="Semantic Cache"
          description="Cache responses for semantically similar queries"
          value={config.semantic_cache_enabled}
          onChange={v => update('semantic_cache_enabled', v)}
        />
        <div className="h-px bg-[#1e2329]" />
        <ConfigToggle
          label="OCR Processing"
          description="Extract text from scanned PDFs and images during ingestion"
          value={config.ocr_enabled}
          onChange={v => update('ocr_enabled', v)}
        />
        <div className="h-px bg-[#1e2329]" />
        <ConfigToggle
          label="Analytics & Telemetry"
          description="Record query events for the analytics dashboard"
          value={config.analytics_enabled}
          onChange={v => update('analytics_enabled', v)}
        />
      </Section>
    </div>
  );
}
