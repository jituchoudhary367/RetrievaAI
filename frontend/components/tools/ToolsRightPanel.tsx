"use client";

import React from 'react';
import { Plus, Download, LayoutTemplate, Key, ChevronRight, ChevronDown, ArrowUp, ArrowDown, Database, Globe, Code, DatabaseBackup } from 'lucide-react';

export function ToolsRightPanel() {
  
  return (
    <div className="flex-1 flex flex-col p-6 space-y-8">
      
      {/* Quick Actions */}
      <div className="flex flex-col space-y-4">
        <span className="text-xs font-semibold text-foreground">Quick Actions</span>
        <div className="flex flex-col space-y-2">
          {[
            { title: 'Create New Tool', sub: 'Build a custom tool', icon: Plus, iconColor: 'text-yellow-500', iconBg: 'bg-yellow-500/10' },
            { title: 'Import Tool', sub: 'Import from JSON or URL', icon: Download, iconColor: 'text-blue-500', iconBg: 'bg-blue-500/10' },
            { title: 'Tool Templates', sub: 'Browse pre-built templates', icon: LayoutTemplate, iconColor: 'text-purple-500', iconBg: 'bg-purple-500/10' },
            { title: 'API Keys', sub: 'Manage connections', icon: Key, iconColor: 'text-green-500', iconBg: 'bg-green-500/10' },
          ].map((act, i) => (
            <div key={i} className="flex items-center justify-between p-3 rounded-lg bg-[#12181f] border border-[#1e2329] hover:border-[#30363d] cursor-pointer group transition-colors">
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

      {/* Tool Categories */}
      <div className="flex flex-col space-y-4 pb-6 border-b border-[#30363d]">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-foreground">Tool Categories</span>
          <span className="text-[10px] text-muted-foreground hover:text-foreground cursor-pointer">View all</span>
        </div>
        
        <div className="flex items-center space-x-4">
          <div className="flex-1 flex flex-col space-y-2.5">
            {[
              { label: 'Retrieval', val: 6, color: 'bg-[#10b981]' },
              { label: 'Search', val: 3, color: 'bg-[#3b82f6]' },
              { label: 'Processing', val: 3, color: 'bg-[#8b5cf6]' },
              { label: 'Data', val: 2, color: 'bg-[#06b6d4]' },
              { label: 'Execution', val: 2, color: 'bg-yellow-500' },
              { label: 'Integration', val: 2, color: 'bg-red-500' },
            ].map(cat => (
              <div key={cat.label} className="flex items-center justify-between text-[10px]">
                <div className="flex items-center space-x-2">
                  <div className={`w-1.5 h-1.5 rounded-full ${cat.color}`} />
                  <span className="text-muted-foreground">{cat.label}</span>
                </div>
                <span className="text-foreground">{cat.val}</span>
              </div>
            ))}
          </div>

          <div className="relative w-20 h-20 flex-shrink-0 mr-2">
            {/* Donut Chart */}
            <svg viewBox="0 0 100 100" className="w-full h-full transform -rotate-90">
              <circle cx="50" cy="50" r="40" fill="transparent" stroke="#1e2329" strokeWidth="16" />
              {/* Retrieval (Green) 33% */}
              <circle cx="50" cy="50" r="40" fill="transparent" stroke="#10b981" strokeWidth="16" strokeDasharray={`${33 * 2.51} 251`} strokeDashoffset="0" />
              {/* Search (Blue) 17% */}
              <circle cx="50" cy="50" r="40" fill="transparent" stroke="#3b82f6" strokeWidth="16" strokeDasharray={`${17 * 2.51} 251`} strokeDashoffset={`-${33 * 2.51}`} />
              {/* Processing (Purple) 17% */}
              <circle cx="50" cy="50" r="40" fill="transparent" stroke="#8b5cf6" strokeWidth="16" strokeDasharray={`${17 * 2.51} 251`} strokeDashoffset={`-${50 * 2.51}`} />
              {/* Others (Yellow approx) 33% */}
              <circle cx="50" cy="50" r="40" fill="transparent" stroke="#eab308" strokeWidth="16" strokeDasharray={`${33 * 2.51} 251`} strokeDashoffset={`-${67 * 2.51}`} />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
              <span className="text-sm font-bold text-foreground">18</span>
              <span className="text-[8px] text-muted-foreground">Total</span>
            </div>
          </div>
        </div>
      </div>

      {/* Usage Overview */}
      <div className="flex flex-col space-y-4 pb-6 border-b border-[#30363d]">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-foreground">Usage Overview</span>
          <div className="flex items-center text-[10px] text-muted-foreground cursor-pointer hover:text-foreground">
            <span>Last 7 days</span>
            <ChevronDown className="w-3 h-3 ml-1" />
          </div>
        </div>
        
        {/* Line Chart */}
        <div className="relative w-full h-20 mt-2">
          {/* Y Axis Labels */}
          <div className="absolute left-0 top-0 bottom-4 flex flex-col justify-between text-[8px] text-muted-foreground z-10">
            <span>2K</span>
            <span>1.5K</span>
            <span>1K</span>
            <span>500</span>
            <span>0</span>
          </div>
          <div className="absolute left-5 right-0 top-1 bottom-4">
             {/* Chart Line */}
             <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="absolute inset-0 w-full h-full overflow-visible">
              <path 
                d="M 0 50 L 16 45 L 33 25 L 50 40 L 66 28 L 83 40 L 100 10" 
                fill="none" 
                stroke="#10b981" 
                strokeWidth="2" 
                vectorEffect="non-scaling-stroke"
              />
              {[
                {x: 0, y: 50}, {x: 16, y: 45}, {x: 33, y: 25}, {x: 50, y: 40}, 
                {x: 66, y: 28}, {x: 83, y: 40}, {x: 100, y: 10}
              ].map((p, i) => (
                <circle key={i} cx={`${p.x}%`} cy={`${p.y}%`} r="3" className="fill-[#10b981] stroke-background stroke-[1.5px]" />
              ))}
            </svg>
          </div>
          {/* X Axis Labels */}
          <div className="absolute bottom-0 left-4 right-0 flex justify-between text-[8px] text-muted-foreground translate-y-1">
            <span>May 19</span><span>May 20</span><span>May 21</span><span>May 22</span><span>May 23</span><span>May 24</span><span>May 25</span>
          </div>
        </div>

        {/* 4 Grid Metrics */}
        <div className="grid grid-cols-2 gap-4 pt-4">
          {[
            { l: 'Total Executions', v: '5,842', t: '28.4%', up: true },
            { l: 'Avg. Daily', v: '834', t: '18.7%', up: true },
            { l: 'Success Rate', v: '98.6%', t: '2.3%', up: true },
            { l: 'Failing Executions', v: '81', t: '9.1%', up: false },
          ].map((m, i) => (
            <div key={i} className="flex flex-col space-y-1">
              <span className="text-[9px] text-muted-foreground">{m.l}</span>
              <span className="text-sm font-bold text-foreground">{m.v}</span>
              <div className={`flex items-center text-[9px] ${m.up ? 'text-[#10b981]' : 'text-red-500'}`}>
                {m.up ? <ArrowUp className="w-2.5 h-2.5 mr-0.5" /> : <ArrowDown className="w-2.5 h-2.5 mr-0.5" />}
                {m.t}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Recent Executions */}
      <div className="flex flex-col space-y-4">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-foreground">Recent Executions</span>
          <span className="text-[10px] text-muted-foreground hover:text-foreground cursor-pointer">View all</span>
        </div>
        
        <div className="flex flex-col space-y-3">
          {[
            { icon: Database, name: 'Vector Search', sub: 'Search across vector database', stat: 'Success', time: '2 min ago', color: 'text-[#10b981]' },
            { icon: Globe, name: 'Web Search', sub: 'Search real-time information from the web', stat: 'Success', time: '15 min ago', color: 'text-[#3b82f6]' },
            { icon: Code, name: 'Code Interpreter', sub: 'Execute code and return results', stat: 'Success', time: '32 min ago', color: 'text-yellow-500' },
            { icon: DatabaseBackup, name: 'SQL Query', sub: 'Query structured data sources using SQL', stat: 'Failed', time: '1 hr ago', color: 'text-[#06b6d4]' },
          ].map((exec, i) => (
            <div key={i} className="flex items-center justify-between group cursor-pointer">
              <div className="flex items-center space-x-2.5">
                <div className={`w-7 h-7 rounded border border-[#30363d] flex items-center justify-center flex-shrink-0 ${exec.color} group-hover:border-[#4b5563] transition-colors`}>
                  <exec.icon className="w-3.5 h-3.5" />
                </div>
                <div className="flex flex-col max-w-[130px]">
                  <span className="text-[10px] font-medium text-foreground truncate">{exec.name}</span>
                  <span className="text-[8px] text-muted-foreground truncate">{exec.sub}</span>
                </div>
              </div>
              <div className="flex flex-col items-end space-y-0.5">
                <span className={`text-[9px] px-1.5 py-0.5 rounded ${exec.stat === 'Success' ? 'text-[#10b981] bg-[#10b981]/10' : 'text-red-500 bg-red-500/10'}`}>
                  {exec.stat}
                </span>
                <span className="text-[8px] text-muted-foreground">{exec.time}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

    </div>
  );
}
