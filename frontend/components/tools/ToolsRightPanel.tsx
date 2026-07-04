"use client";

import React, { useState } from 'react';
import { Plus, Download, LayoutTemplate, Key, ChevronRight, Database, Globe, Code } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { ToolRow, ToolExecutionRow } from '../../lib/types/backend';
import { toolsApi } from '../../lib/api/tools';

const TOOL_ICONS: Record<string, React.ElementType> = {
  vector_search: Database,
  web_search: Globe,
  code_search: Code,
};

const CAT_COLORS: Record<string, string> = {
  Retrieval: '#10b981',
  Search: '#3b82f6',
  Processing: '#8b5cf6',
  Execution: '#eab308',
  Data: '#06b6d4',
  Integration: '#ef4444',
};

interface Props {
  tools: ToolRow[];
  recentExecutions: ToolExecutionRow[];
  showRegisterModal: () => void;
}

export function ToolsRightPanel({ tools, recentExecutions, showRegisterModal }: Props) {
  const router = useRouter();

  // Compute real category counts
  const categoryCounts: Record<string, number> = {};
  tools.forEach(t => {
    const cat = t.category || 'Other';
    categoryCounts[cat] = (categoryCounts[cat] || 0) + 1;
  });
  const catEntries = Object.entries(categoryCounts).sort((a, b) => b[1] - a[1]);
  const totalCats = tools.length;

  // Donut segments from real data
  let offset = 0;
  const segments = catEntries.map(([cat, count]) => {
    const pct = totalCats > 0 ? (count / totalCats) * 100 : 0;
    const seg = { cat, count, pct, color: CAT_COLORS[cat] || '#9ca3af', offset };
    offset += pct;
    return seg;
  });

  const getIcon = (tool: ToolRow): React.ElementType => {
    const key = tool.name.toLowerCase().replace(/\s+/g, '_');
    return TOOL_ICONS[key] || Database;
  };

  const getRelTime = (iso: string) => {
    const diff = Date.now() - new Date(iso).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'Just now';
    if (mins < 60) return `${mins} min ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs} hr ago`;
    return `${Math.floor(hrs / 24)} day ago`;
  };

  return (
    <div className="flex-1 flex flex-col p-6 space-y-8">
      
      {/* Quick Actions */}
      <div className="flex flex-col space-y-4">
        <span className="text-xs font-semibold text-foreground">Quick Actions</span>
        <div className="flex flex-col space-y-2">
          {[
            { title: 'Register New Tool', sub: 'Register tool metadata', icon: Plus, iconColor: 'text-yellow-500', iconBg: 'bg-yellow-500/10', action: showRegisterModal },
            { title: 'Import Tool', sub: 'Import from JSON or URL', icon: Download, iconColor: 'text-blue-500', iconBg: 'bg-blue-500/10', action: undefined },
            { title: 'Tool Templates', sub: 'Browse pre-built templates', icon: LayoutTemplate, iconColor: 'text-purple-500', iconBg: 'bg-purple-500/10', action: undefined },
            { title: 'API Keys', sub: 'Manage connections', icon: Key, iconColor: 'text-green-500', iconBg: 'bg-green-500/10', action: () => router.push('/settings') },
          ].map((act, i) => (
            <div
              key={i}
              className="flex items-center justify-between p-3 rounded-lg bg-[#12181f] border border-[#1e2329] hover:border-[#30363d] cursor-pointer group transition-colors"
              onClick={act.action}
            >
              <div className="flex items-center space-x-3">
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${act.iconBg} ${act.iconColor}`}>
                  <act.icon className="w-4 h-4" strokeWidth={2} />
                </div>
                <div className="flex flex-col">
                  <span className="text-[11px] font-medium text-foreground group-hover:text-primary transition-colors">{act.title}</span>
                  <span className="text-[9px] text-muted-foreground">{act.sub}</span>
                </div>
              </div>
              <ChevronRight className="w-3.5 h-3.5 text-muted-foreground group-hover:text-foreground transition-colors" />
            </div>
          ))}
        </div>
      </div>

      {/* Tool Categories — real data */}
      {tools.length > 0 && (
        <div className="flex flex-col space-y-4 pb-6 border-b border-[#30363d]">
          <span className="text-xs font-semibold text-foreground">Tool Categories</span>
          <div className="flex items-center space-x-4">
            <div className="flex-1 flex flex-col space-y-2.5">
              {catEntries.map(([cat, count]) => (
                <div key={cat} className="flex items-center justify-between text-[10px]">
                  <div className="flex items-center space-x-2">
                    <div className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: CAT_COLORS[cat] || '#9ca3af' }} />
                    <span className="text-muted-foreground">{cat}</span>
                  </div>
                  <span className="text-foreground">{count}</span>
                </div>
              ))}
            </div>

            <div className="relative w-20 h-20 flex-shrink-0 mr-2">
              <svg viewBox="0 0 100 100" className="w-full h-full transform -rotate-90">
                <circle cx="50" cy="50" r="40" fill="transparent" stroke="#1e2329" strokeWidth="16" />
                {segments.map((seg, i) => (
                  <circle
                    key={i}
                    cx="50" cy="50" r="40" fill="transparent"
                    stroke={seg.color}
                    strokeWidth="16"
                    strokeDasharray={`${seg.pct * 2.51} 251`}
                    strokeDashoffset={`-${seg.offset * 2.51}`}
                  />
                ))}
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                <span className="text-sm font-bold text-foreground">{totalCats}</span>
                <span className="text-[8px] text-muted-foreground">Total</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Recent Executions — real data */}
      <div className="flex flex-col space-y-4">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-foreground">Recent Executions</span>
        </div>
        <div className="flex flex-col space-y-3">
          {recentExecutions.length === 0 ? (
            <span className="text-[10px] text-muted-foreground">No executions recorded yet</span>
          ) : (
            recentExecutions.slice(0, 5).map((exec, i) => {
              const tool = tools.find(t => t.id === exec.toolId);
              const Icon = tool ? getIcon(tool) : Database;
              return (
                <div key={i} className="flex items-center justify-between group cursor-pointer">
                  <div className="flex items-center space-x-2.5">
                    <div className="w-7 h-7 rounded border border-[#30363d] flex items-center justify-center flex-shrink-0 text-[#10b981] group-hover:border-[#4b5563] transition-colors">
                      <Icon className="w-3.5 h-3.5" />
                    </div>
                    <div className="flex flex-col max-w-[130px]">
                      <span className="text-[10px] font-medium text-foreground truncate">
                        {tool?.name?.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()) || 'Unknown Tool'}
                      </span>
                      <span className="text-[8px] text-muted-foreground truncate">{tool?.description || '—'}</span>
                    </div>
                  </div>
                  <div className="flex flex-col items-end space-y-0.5">
                    <span className={`text-[9px] px-1.5 py-0.5 rounded ${
                      exec.status === 'success'
                        ? 'text-[#10b981] bg-[#10b981]/10'
                        : 'text-red-500 bg-red-500/10'
                    }`}>
                      {exec.status === 'success' ? 'Success' : 'Failed'}
                    </span>
                    <span className="text-[8px] text-muted-foreground">{getRelTime(exec.createdAt)}</span>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
