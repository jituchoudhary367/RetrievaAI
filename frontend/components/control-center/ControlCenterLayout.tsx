'use client';

import React, { useState } from 'react';
import {
  Cpu, Database, Search, Plug, Sliders, Key, Shield, User,
  ChevronRight, Activity, Zap, BarChart3, Settings2
} from 'lucide-react';

export type CCTab =
  | 'providers'
  | 'models'
  | 'embeddings'
  | 'search'
  | 'connectors'
  | 'runtime'
  | 'keys'
  | 'security'
  | 'account';

interface Tab {
  id: CCTab;
  label: string;
  icon: React.ReactNode;
  badge?: string;
}

const TABS: Tab[] = [
  { id: 'providers',  label: 'AI Providers',    icon: <Cpu size={15} />,      badge: 'LLM' },
  { id: 'models',     label: 'Model Hub',        icon: <Zap size={15} />,      badge: 'Dynamic' },
  { id: 'embeddings', label: 'Embeddings',       icon: <Database size={15} /> },
  { id: 'search',     label: 'Search',           icon: <Search size={15} /> },
  { id: 'connectors', label: 'Connectors',       icon: <Plug size={15} /> },
  { id: 'runtime',    label: 'Runtime Config',   icon: <Sliders size={15} /> },
  { id: 'keys',       label: 'API Keys',         icon: <Key size={15} /> },
  { id: 'security',   label: 'Security',         icon: <Shield size={15} /> },
  { id: 'account',    label: 'Account',          icon: <User size={15} /> },
];

interface Props {
  activeTab: CCTab;
  onTabChange: (tab: CCTab) => void;
  children: React.ReactNode;
  rightSidebar?: React.ReactNode;
}

export function ControlCenterLayout({ activeTab, onTabChange, children, rightSidebar }: Props) {
  return (
    <div className="flex h-full w-full overflow-hidden">
      {/* ── Left Sidebar / Tab Nav ── */}
      <aside className="w-52 shrink-0 flex flex-col border-r border-[#1e2329] bg-[#0d1117] overflow-y-auto">
        {/* Header */}
        <div className="px-4 pt-5 pb-3">
          <div className="flex items-center gap-2 mb-1">
            <Settings2 size={16} className="text-emerald-400" />
            <span className="text-xs font-bold text-emerald-400 uppercase tracking-widest">Control Center</span>
          </div>
          <p className="text-[10px] text-[#4a5568] leading-tight">Workspace Configuration</p>
        </div>

        {/* Divider */}
        <div className="mx-4 mb-3 h-px bg-[#1e2329]" />

        {/* Nav items */}
        <nav className="flex-1 px-2 space-y-0.5">
          {TABS.map(tab => (
            <button
              key={tab.id}
              onClick={() => onTabChange(tab.id)}
              className={`
                w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium transition-all duration-150 text-left
                ${activeTab === tab.id
                  ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                  : 'text-[#8b9499] hover:text-white hover:bg-white/5 border border-transparent'
                }
              `}
            >
              <span className={activeTab === tab.id ? 'text-emerald-400' : 'text-[#4a5568]'}>
                {tab.icon}
              </span>
              <span className="flex-1">{tab.label}</span>
              {tab.badge && (
                <span className="text-[9px] px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 font-semibold">
                  {tab.badge}
                </span>
              )}
              {activeTab === tab.id && <ChevronRight size={12} className="text-emerald-400 shrink-0" />}
            </button>
          ))}
        </nav>

        {/* Footer */}
        <div className="px-4 py-3 border-t border-[#1e2329]">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-[10px] text-[#4a5568]">All systems operational</span>
          </div>
        </div>
      </aside>

      {/* ── Main Content ── */}
      <main className="flex-1 min-w-0 overflow-y-auto bg-[#0d1117]">
        <div className="p-6 max-w-4xl">
          {children}
        </div>
      </main>

      {/* ── Right Sidebar ── */}
      {rightSidebar && (
        <aside className="w-64 shrink-0 border-l border-[#1e2329] bg-[#0d1117] overflow-y-auto">
          {rightSidebar}
        </aside>
      )}
    </div>
  );
}
