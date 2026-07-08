'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { workspaceApi, WorkspaceUsage } from '@/lib/api/workspace';
import { Activity, Zap, Database, BarChart3, Clock, RefreshCw, TrendingUp, MessageSquare } from 'lucide-react';

// ── Health Sidebar ─────────────────────────────────────────────────────────────

interface ServiceHealth {
  name: string;
  status: 'healthy' | 'degraded' | 'down' | 'unknown';
  latency_ms?: number;
}

function ServiceRow({ name, status, latency_ms }: ServiceHealth) {
  const dot: Record<string, string> = {
    healthy: 'bg-emerald-400',
    degraded: 'bg-yellow-400',
    down: 'bg-red-400',
    unknown: 'bg-[#4a5568]',
  };
  const text: Record<string, string> = {
    healthy: 'text-emerald-400',
    degraded: 'text-yellow-400',
    down: 'text-red-400',
    unknown: 'text-[#4a5568]',
  };
  return (
    <div className="flex items-center justify-between py-1.5">
      <div className="flex items-center gap-2">
        <span className={`w-1.5 h-1.5 rounded-full ${dot[status] ?? dot.unknown}`} />
        <span className="text-[11px] text-[#8b9499]">{name}</span>
      </div>
      <div className="flex items-center gap-1.5">
        {latency_ms != null && (
          <span className="text-[10px] text-[#4a5568]">{latency_ms.toFixed(0)}ms</span>
        )}
        <span className={`text-[10px] font-medium capitalize ${text[status] ?? text.unknown}`}>{status}</span>
      </div>
    </div>
  );
}

export function HealthSidebar() {
  const [health, setHealth] = useState<Record<string, any> | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try {
      const h = await workspaceApi.getHealth();
      setHealth(h);
    } catch { /* ignore */ }
    setLoading(false);
  }, []);

  useEffect(() => {
    load();
    const t = setInterval(load, 30_000);
    return () => clearInterval(t);
  }, [load]);

  const services: ServiceHealth[] = health
    ? [
        { name: 'API Server', status: 'healthy' },
        { name: 'PostgreSQL', status: health.postgres?.status ?? 'unknown', latency_ms: health.postgres?.latency_ms },
        { name: 'Redis', status: health.redis?.status ?? 'unknown', latency_ms: health.redis?.latency_ms },
        { name: 'Qdrant', status: health.qdrant?.status ?? 'unknown', latency_ms: health.qdrant?.latency_ms },
        { name: 'Celery', status: health.celery?.status ?? 'unknown' },
        { name: 'LLM Provider', status: health.llm?.status ?? 'unknown', latency_ms: health.llm?.latency_ms },
        { name: 'Embedding', status: health.embedding?.status ?? 'unknown', latency_ms: health.embedding?.latency_ms },
      ]
    : [];

  const allHealthy = services.length > 0 && services.every(s => s.status === 'healthy');
  const anyDown = services.some(s => s.status === 'down');

  return (
    <div className="p-4 space-y-4">
      {/* System Status */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-1.5">
            <Activity size={13} className="text-emerald-400" />
            <span className="text-[11px] font-bold text-white uppercase tracking-wider">System Health</span>
          </div>
          <button onClick={load} className="p-1 rounded text-[#4a5568] hover:text-white transition-colors">
            <RefreshCw size={11} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>

        {/* Overall status banner */}
        <div className={`flex items-center gap-2 px-3 py-2 rounded-lg mb-3 ${
          anyDown ? 'bg-red-500/5 border border-red-500/15' :
          allHealthy ? 'bg-emerald-500/5 border border-emerald-500/15' :
          'bg-yellow-500/5 border border-yellow-500/15'
        }`}>
          <span className={`w-2 h-2 rounded-full ${anyDown ? 'bg-red-400' : allHealthy ? 'bg-emerald-400 animate-pulse' : 'bg-yellow-400'}`} />
          <span className={`text-[10px] font-medium ${anyDown ? 'text-red-400' : allHealthy ? 'text-emerald-400' : 'text-yellow-400'}`}>
            {anyDown ? 'Service degraded' : allHealthy ? 'All systems operational' : 'Partial degradation'}
          </span>
        </div>

        <div className="space-y-0.5 divide-y divide-[#1e2329]/50">
          {loading && services.length === 0
            ? Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="flex items-center justify-between py-1.5 animate-pulse">
                  <div className="h-3 w-20 bg-[#1e2329] rounded" />
                  <div className="h-3 w-12 bg-[#1e2329] rounded" />
                </div>
              ))
            : services.map(s => <ServiceRow key={s.name} {...s} />)
          }
        </div>
      </div>
    </div>
  );
}

// ── Usage Sidebar ──────────────────────────────────────────────────────────────

function StatCard({ icon: Icon, label, value, sub }: {
  icon: React.ElementType; label: string; value: string; sub?: string;
}) {
  return (
    <div className="bg-[#12181f] border border-[#1e2329] rounded-xl p-3 space-y-1">
      <div className="flex items-center gap-1.5">
        <Icon size={12} className="text-emerald-400" />
        <span className="text-[10px] text-[#4a5568]">{label}</span>
      </div>
      <p className="text-sm font-bold text-white">{value}</p>
      {sub && <p className="text-[10px] text-[#4a5568]">{sub}</p>}
    </div>
  );
}

export function UsageSidebar({ days = 7 }: { days?: number }) {
  const [usage, setUsage] = useState<WorkspaceUsage | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    workspaceApi.getUsage(days)
      .then(setUsage)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [days]);

  const fmt = (n: number) =>
    n >= 1_000_000 ? `${(n / 1_000_000).toFixed(1)}M`
    : n >= 1_000 ? `${(n / 1_000).toFixed(1)}K`
    : String(n);

  return (
    <div className="p-4 border-t border-[#1e2329] space-y-3">
      <div className="flex items-center gap-1.5">
        <BarChart3 size={13} className="text-emerald-400" />
        <span className="text-[11px] font-bold text-white uppercase tracking-wider">Usage ({days}d)</span>
      </div>

      {loading ? (
        <div className="grid grid-cols-2 gap-2">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-16 bg-[#12181f] border border-[#1e2329] rounded-xl animate-pulse" />
          ))}
        </div>
      ) : usage ? (
        <div className="grid grid-cols-2 gap-2">
          <StatCard icon={MessageSquare} label="Queries" value={fmt(usage.total_queries)} sub={`Last ${days} days`} />
          <StatCard icon={Zap} label="Cache Hit" value={`${usage.cache_hit_rate.toFixed(0)}%`} sub={`${usage.cache_hits} hits`} />
          <StatCard icon={Database} label="Tokens" value={fmt(usage.total_tokens)} />
          <StatCard icon={Clock} label="Avg Latency" value={`${usage.avg_latency_ms.toFixed(0)}ms`} />
        </div>
      ) : (
        <p className="text-[10px] text-[#4a5568]">No usage data available</p>
      )}
    </div>
  );
}
