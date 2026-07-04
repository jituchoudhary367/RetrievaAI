"use client";

import React, { useState } from 'react';
import { Search, ChevronDown, LayoutGrid, List, Play, Settings, MoreVertical, Database, Globe, Code } from 'lucide-react';
import { ToolRow, ToolExecutionRow } from '../../lib/types/backend';

// Icon map keyed by tool name — only map the 3 real seeded tools
const TOOL_ICONS: Record<string, React.ElementType> = {
  vector_search: Database,
  web_search: Globe,
  code_search: Code,
};

const CAT_COLORS: Record<string, string> = {
  Retrieval: 'text-[#10b981] bg-[#10b981]/10 border-[#10b981]/20',
  Search: 'text-[#3b82f6] bg-[#3b82f6]/10 border-[#3b82f6]/20',
  Processing: 'text-[#8b5cf6] bg-[#8b5cf6]/10 border-[#8b5cf6]/20',
  Execution: 'text-yellow-500 bg-yellow-500/10 border-yellow-500/20',
  Data: 'text-[#06b6d4] bg-[#06b6d4]/10 border-[#06b6d4]/20',
};

interface Props {
  tools: ToolRow[];
  executions: Record<string, ToolExecutionRow[]>; // toolId → recent executions
}

const SuccessRing = ({ rate, colorClass }: { rate: number; colorClass: string }) => (
  <div className="relative w-4 h-4 ml-3">
    <svg viewBox="0 0 24 24" className="w-full h-full transform -rotate-90">
      <circle cx="12" cy="12" r="10" fill="transparent" stroke="#30363d" strokeWidth="3" />
      <circle
        cx="12" cy="12" r="10" fill="transparent"
        className={colorClass.replace('text-', 'stroke-')}
        strokeWidth="3"
        strokeDasharray={`${(rate / 100) * 62.8} 62.8`}
      />
    </svg>
  </div>
);

export function ToolListArea({ tools, executions }: Props) {
  const [searchQuery, setSearchQuery] = useState('');

  const filtered = tools.filter(t =>
    t.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    t.description?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    t.category?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const getIcon = (tool: ToolRow): React.ElementType => {
    const key = tool.name.toLowerCase().replace(/\s+/g, '_');
    return TOOL_ICONS[key] || Database;
  };

  const getCatColor = (cat: string) => CAT_COLORS[cat] || 'text-muted-foreground bg-muted border-border';

  const getSuccessRate = (toolId: string): number => {
    const execs = executions[toolId] || [];
    if (execs.length === 0) return 0;
    const successes = execs.filter(e => e.status === 'success').length;
    return Math.round((successes / execs.length) * 100 * 10) / 10;
  };

  const getLastUsed = (toolId: string): string => {
    const execs = executions[toolId] || [];
    if (execs.length === 0) return 'Never';
    const latest = execs.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())[0];
    const diff = Date.now() - new Date(latest.createdAt).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'Just now';
    if (mins < 60) return `${mins} min ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs} hr ago`;
    return `${Math.floor(hrs / 24)} day ago`;
  };

  return (
    <div className="flex flex-col bg-[#12181f] border border-[#1e2329] rounded-xl overflow-hidden flex-1 min-h-[500px]">
      
      {/* Filters */}
      <div className="p-4 border-b border-[#1e2329] flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex items-center space-x-3 w-full md:w-auto">
          <div className="relative w-full md:w-72">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search tools by name, description or category..."
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              className="w-full bg-[#161b22] border border-[#30363d] rounded-md pl-9 pr-3 py-1.5 text-xs text-foreground placeholder-muted-foreground focus:outline-none focus:border-[#4b5563] transition-colors"
            />
          </div>
        </div>

        <div className="flex items-center space-x-4 w-full md:w-auto justify-end">
          <div className="flex items-center border border-[#30363d] rounded-md p-0.5">
            <button className="p-1 rounded hover:bg-[#21262d] text-muted-foreground transition-colors"><LayoutGrid className="w-3.5 h-3.5" /></button>
            <button className="p-1 rounded bg-[#21262d] text-foreground shadow-sm"><List className="w-3.5 h-3.5" /></button>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead className="text-[10px] text-muted-foreground border-b border-[#1e2329]">
            <tr>
              <th className="px-6 py-4 font-medium">Tool</th>
              <th className="px-6 py-4 font-medium w-32">Category</th>
              <th className="px-6 py-4 font-medium w-28">Status</th>
              <th className="px-6 py-4 font-medium w-32">Success Rate</th>
              <th className="px-6 py-4 font-medium w-28">Last Used</th>
              <th className="px-6 py-4 font-medium text-right w-32">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#1e2329]/50">
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-6 py-12 text-center text-muted-foreground text-xs">
                  {searchQuery ? 'No tools match your search' : 'No tools registered yet'}
                </td>
              </tr>
            ) : (
              filtered.map(tool => {
                const Icon = getIcon(tool);
                const catColor = getCatColor(tool.category || '');
                const sr = getSuccessRate(tool.id);
                const lastUsed = getLastUsed(tool.id);

                return (
                  <tr key={tool.id} className="hover:bg-[#1a212a] transition-colors group">
                    <td className="px-6 py-4">
                      <div className="flex items-center space-x-3">
                        <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${catColor}`}>
                          <Icon className="h-4 w-4" strokeWidth={2} />
                        </div>
                        <div className="flex flex-col">
                          <span className="font-semibold text-foreground group-hover:text-primary transition-colors cursor-pointer">
                            {tool.name.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                          </span>
                          <span className="text-[10px] text-muted-foreground">{tool.description || '—'}</span>
                        </div>
                      </div>
                    </td>

                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded text-[9px] border ${catColor}`}>
                        {tool.category || 'General'}
                      </span>
                    </td>

                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded text-[9px] border ${
                        tool.status === 'active'
                          ? 'text-[#10b981] bg-[#10b981]/10 border-[#10b981]/20'
                          : 'text-muted-foreground bg-[#21262d] border-[#30363d]'
                      }`}>
                        {tool.status === 'active' ? 'Active' : 'Inactive'}
                      </span>
                    </td>

                    <td className="px-6 py-4">
                      <div className="flex items-center text-foreground font-medium">
                        {sr}%
                        <SuccessRing rate={sr} colorClass={catColor.split(' ')[0]} />
                      </div>
                    </td>

                    <td className="px-6 py-4 text-muted-foreground">{lastUsed}</td>

                    <td className="px-6 py-4 text-right">
                      <div className="flex items-center justify-end space-x-2 opacity-60 group-hover:opacity-100 transition-opacity">
                        <button className="p-1.5 rounded hover:bg-[#21262d] text-muted-foreground hover:text-foreground transition-colors border border-transparent hover:border-[#30363d]" title="Test tool">
                          <Play className="w-3 h-3" />
                        </button>
                        <button className="p-1.5 rounded hover:bg-[#21262d] text-muted-foreground hover:text-foreground transition-colors border border-transparent hover:border-[#30363d]" title="Settings">
                          <Settings className="w-3 h-3" />
                        </button>
                        <button className="p-1.5 rounded hover:bg-[#21262d] text-muted-foreground hover:text-foreground transition-colors border border-transparent hover:border-[#30363d]" title="More">
                          <MoreVertical className="w-3 h-3" />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Footer */}
      <div className="px-6 py-4 border-t border-[#1e2329] flex items-center justify-between text-[10px] text-muted-foreground mt-auto bg-[#12181f]">
        <span>Showing {filtered.length} of {tools.length} tool{tools.length !== 1 ? 's' : ''}</span>
      </div>
    </div>
  );
}
