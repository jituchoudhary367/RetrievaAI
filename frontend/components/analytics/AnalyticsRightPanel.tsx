"use client";

import React from 'react';
import { CheckCircle2, AlertTriangle, XCircle, ChevronRight } from 'lucide-react';
import { useHealthPolling } from '../../lib/hooks/useHealthPolling';

interface TopQuery {
  query: string;
  intent: string;
  timestamp: string;
}

interface Props {
  topQueries: TopQuery[];
}

const QUERY_COLORS = ['bg-[#10b981]/20 text-[#10b981]', 'bg-[#3b82f6]/20 text-[#3b82f6]', 'bg-[#8b5cf6]/20 text-[#8b5cf6]', 'bg-yellow-500/20 text-yellow-500', 'bg-[#f97316]/20 text-[#f97316]'];

export function AnalyticsRightPanel({ topQueries }: Props) {
  const { health, error: healthError } = useHealthPolling(30000);

  const overallStatus = health?.status || (healthError ? 'unhealthy' : null);
  const statusLabel = overallStatus === 'healthy'
    ? 'All systems operational'
    : overallStatus === 'degraded'
    ? 'Some systems degraded'
    : overallStatus === 'unhealthy'
    ? 'System issues detected'
    : 'Checking...';

  const StatusIcon = overallStatus === 'healthy'
    ? CheckCircle2
    : overallStatus === 'degraded'
    ? AlertTriangle
    : XCircle;

  const statusIconColor = overallStatus === 'healthy'
    ? 'text-[#10b981]'
    : overallStatus === 'degraded'
    ? 'text-yellow-500'
    : 'text-red-500';

  const getDotColor = (status: string) => {
    if (status === 'healthy') return 'bg-[#10b981]';
    if (status === 'degraded') return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const getStatusText = (status: string) => {
    if (status === 'healthy') return 'Healthy';
    if (status === 'degraded') return 'Degraded';
    return 'Down';
  };

  const getStatusTextColor = (status: string) => {
    if (status === 'healthy') return 'text-[#10b981]';
    if (status === 'degraded') return 'text-yellow-500';
    return 'text-red-500';
  };

  const getRelTime = (iso: string) => {
    const diff = Date.now() - new Date(iso).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'Just now';
    if (mins < 60) return `${mins}m ago`;
    return `${Math.floor(mins / 60)}h ago`;
  };

  return (
    <div className="flex-1 flex flex-col p-6 space-y-6">
      
      {/* System Health — from useHealthPolling */}
      <div className="flex flex-col space-y-4 pb-6 border-b border-[#30363d]">
        <span className="text-xs font-semibold text-foreground">System Health</span>
        <div className="flex items-center space-x-2 text-[10px] text-muted-foreground -mt-2">
          <span>{statusLabel}</span>
          <StatusIcon className={`w-3.5 h-3.5 ${statusIconColor}`} />
        </div>
        
        <div className="flex flex-col space-y-2.5">
          {health?.components && health.components.length > 0 ? (
            health.components.map(comp => (
              <div key={comp.name} className="flex items-center justify-between text-[10px]">
                <div className="flex items-center space-x-2">
                  <div className={`w-1.5 h-1.5 rounded-full ${getDotColor(comp.status)}`} />
                  <span className="text-muted-foreground capitalize">{comp.name}</span>
                </div>
                <span className={getStatusTextColor(comp.status)}>
                  {getStatusText(comp.status)}
                </span>
              </div>
            ))
          ) : (
            <span className="text-[10px] text-muted-foreground">
              {healthError ? 'Unable to reach backend' : 'Loading...'}
            </span>
          )}
        </div>
      </div>

      {/* Top Queries — real data */}
      <div className="flex flex-col space-y-4 pb-6 border-b border-[#30363d]">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-foreground">Recent Queries</span>
        </div>
        
        <div className="flex flex-col space-y-3 text-[10px]">
          {topQueries.length === 0 ? (
            <span className="text-muted-foreground">No queries yet</span>
          ) : (
            topQueries.slice(0, 5).map((item, i) => (
              <div key={i} className="flex items-center justify-between group cursor-pointer">
                <div className="flex items-center space-x-2 overflow-hidden pr-2">
                  <div className={`w-3.5 h-3.5 rounded flex items-center justify-center flex-shrink-0 text-[8px] font-bold ${QUERY_COLORS[i % QUERY_COLORS.length]}`}>
                    {i + 1}
                  </div>
                  <span className="text-muted-foreground group-hover:text-foreground transition-colors truncate" title={item.query}>
                    {item.query}
                  </span>
                </div>
                <div className="flex-shrink-0 text-muted-foreground ml-2">
                  {getRelTime(item.timestamp)}
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Cost Breakdown — labeled as estimated, no fake numbers */}
      <div className="flex flex-col space-y-4 pb-6">
        <span className="text-xs font-semibold text-foreground">Cost Breakdown (Estimated)</span>
        <div className="flex items-center justify-center p-6 text-center text-[10px] text-muted-foreground bg-[#12181f] rounded-lg border border-[#1e2329]">
          Cost tracking requires a billing API key.<br />
          Configure in Settings → Integrations.
        </div>
      </div>
    </div>
  );
}
