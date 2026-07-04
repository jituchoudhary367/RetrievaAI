"use client";

import React, { useState } from 'react';
import { Settings, Server, Database, BarChart2, ChevronDown, Moon, Sun, Monitor, ChevronsUpDown } from 'lucide-react';

export function SettingsGrid() {

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      
      {/* General Preferences */}
      <div className="bg-[#12181f] border border-[#1e2329] rounded-xl flex flex-col overflow-hidden">
        <div className="p-5 border-b border-[#1e2329] flex items-center space-x-3 bg-[#12181f]">
          <div className="w-10 h-10 rounded-lg bg-[#10b981]/10 flex items-center justify-center flex-shrink-0 border border-[#10b981]/20">
            <Settings className="w-5 h-5 text-[#10b981]" strokeWidth={1.5} />
          </div>
          <div className="flex flex-col">
            <h3 className="text-sm font-semibold text-foreground">General Preferences</h3>
            <p className="text-[11px] text-muted-foreground">Configure basic system preferences</p>
          </div>
        </div>
        
        <div className="p-5 flex flex-col space-y-6 flex-1">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div className="flex flex-col">
              <span className="text-xs font-medium text-foreground">System Name</span>
              <span className="text-[10px] text-muted-foreground">The name of your RetrievaAI system</span>
            </div>
            <input 
              type="text" 
              defaultValue="RetrievaAI"
              className="bg-[#161b22] border border-[#30363d] rounded-md px-3 py-1.5 text-xs text-foreground focus:outline-none focus:border-[#4b5563] sm:w-56"
            />
          </div>

          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div className="flex flex-col">
              <span className="text-xs font-medium text-foreground">Default Language</span>
              <span className="text-[10px] text-muted-foreground">Default language for responses</span>
            </div>
            <div className="relative sm:w-56">
              <GlobeIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground" />
              <select className="w-full appearance-none bg-[#161b22] border border-[#30363d] rounded-md pl-9 pr-8 py-1.5 text-xs text-foreground focus:outline-none focus:border-[#4b5563]">
                <option>English (US)</option>
              </select>
              <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground pointer-events-none" />
            </div>
          </div>

          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div className="flex flex-col">
              <span className="text-xs font-medium text-foreground">Timezone</span>
              <span className="text-[10px] text-muted-foreground">System timezone</span>
            </div>
            <div className="relative sm:w-56">
              <select className="w-full appearance-none bg-[#161b22] border border-[#30363d] rounded-md pl-3 pr-8 py-1.5 text-xs text-foreground focus:outline-none focus:border-[#4b5563]">
                <option>(GMT+5:30) Asia/Kolkata</option>
              </select>
              <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground pointer-events-none" />
            </div>
          </div>

          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div className="flex flex-col">
              <span className="text-xs font-medium text-foreground">Date Format</span>
              <span className="text-[10px] text-muted-foreground">Choose your preferred date format</span>
            </div>
            <div className="relative sm:w-56">
              <select className="w-full appearance-none bg-[#161b22] border border-[#30363d] rounded-md pl-3 pr-8 py-1.5 text-xs text-foreground focus:outline-none focus:border-[#4b5563]">
                <option>May 25, 2024 (MMM DD, YYYY)</option>
              </select>
              <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground pointer-events-none" />
            </div>
          </div>

          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-t border-[#1e2329]/50 pt-6">
            <div className="flex flex-col">
              <span className="text-xs font-medium text-foreground">Theme</span>
              <span className="text-[10px] text-muted-foreground">Choose your preferred theme</span>
            </div>
            <div className="flex items-center p-0.5 bg-[#161b22] border border-[#30363d] rounded-md">
              <button className="flex items-center space-x-1.5 px-3 py-1 rounded bg-[#21262d] border border-[#10b981]/30 text-primary shadow-sm text-[11px] font-medium transition-colors">
                <Moon className="w-3.5 h-3.5" />
                <span>Dark</span>
              </button>
              <button className="flex items-center space-x-1.5 px-3 py-1 rounded text-muted-foreground hover:text-foreground hover:bg-[#21262d] text-[11px] font-medium transition-colors border border-transparent">
                <Sun className="w-3.5 h-3.5" />
                <span>Light</span>
              </button>
              <button className="flex items-center space-x-1.5 px-3 py-1 rounded text-muted-foreground hover:text-foreground hover:bg-[#21262d] text-[11px] font-medium transition-colors border border-transparent">
                <Monitor className="w-3.5 h-3.5" />
                <span>System</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* System Configuration */}
      <div className="bg-[#12181f] border border-[#1e2329] rounded-xl flex flex-col overflow-hidden">
        <div className="p-5 border-b border-[#1e2329] flex items-center space-x-3 bg-[#12181f]">
          <div className="w-10 h-10 rounded-lg bg-[#8b5cf6]/10 flex items-center justify-center flex-shrink-0 border border-[#8b5cf6]/20">
            <Server className="w-5 h-5 text-[#8b5cf6]" strokeWidth={1.5} />
          </div>
          <div className="flex flex-col">
            <h3 className="text-sm font-semibold text-foreground">System Configuration</h3>
            <p className="text-[11px] text-muted-foreground">Configure core system settings</p>
          </div>
        </div>
        
        <div className="p-5 flex flex-col space-y-6 flex-1">
          {[
            { label: 'Max Tokens per Request', sub: 'Maximum tokens for LLM requests', val: '8,192' },
            { label: 'Response Timeout', sub: 'LLM response timeout in seconds', val: '60 sec' },
            { label: 'Max File Size', sub: 'Maximum file size for uploads', val: '200 MB' },
            { label: 'Chunk Size', sub: 'Default chunk size for processing', val: '1,024 tokens' },
            { label: 'Chunk Overlap', sub: 'Default overlap between chunks', val: '200 tokens' },
          ].map((item, i) => (
            <div key={i} className={`flex flex-col sm:flex-row sm:items-center justify-between gap-2 ${i === 3 ? 'border-t border-[#1e2329]/50 pt-6' : ''}`}>
              <div className="flex flex-col">
                <span className="text-xs font-medium text-foreground">{item.label}</span>
                <span className="text-[10px] text-muted-foreground">{item.sub}</span>
              </div>
              <div className="relative sm:w-32">
                <input 
                  type="text" 
                  defaultValue={item.val}
                  className="w-full bg-[#161b22] border border-[#30363d] rounded-md pl-3 pr-8 py-1.5 text-xs text-foreground text-right focus:outline-none focus:border-[#4b5563]"
                />
                <ChevronsUpDown className="absolute right-2 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground opacity-50" />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Data & Storage */}
      <div className="bg-[#12181f] border border-[#1e2329] rounded-xl flex flex-col overflow-hidden">
        <div className="p-5 border-b border-[#1e2329] flex items-center space-x-3 bg-[#12181f]">
          <div className="w-10 h-10 rounded-lg bg-yellow-500/10 flex items-center justify-center flex-shrink-0 border border-yellow-500/20">
            <Database className="w-5 h-5 text-yellow-500" strokeWidth={1.5} />
          </div>
          <div className="flex flex-col">
            <h3 className="text-sm font-semibold text-foreground">Data & Storage</h3>
            <p className="text-[11px] text-muted-foreground">Manage storage and data settings</p>
          </div>
        </div>
        
        <div className="p-5 flex flex-col space-y-6 flex-1">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div className="flex flex-col">
              <span className="text-xs font-medium text-foreground">Vector Database</span>
              <span className="text-[10px] text-muted-foreground">Primary vector database</span>
            </div>
            <div className="flex items-center space-x-3 sm:w-56 justify-end sm:justify-between">
              <span className="text-xs font-medium text-foreground hidden sm:block">Qdrant</span>
              <span className="text-[10px] text-primary bg-[#10b981]/10 px-2 py-0.5 rounded border border-[#10b981]/20 font-medium">Connected</span>
            </div>
          </div>

          {[
            { label: 'Embedding Model', sub: 'Default embedding model', val: 'bge-large-en-v1.5' },
            { label: 'Storage Location', sub: 'Document storage location', val: 'Local Storage' },
            { label: 'Backup Frequency', sub: 'Automatic backup frequency', val: 'Daily' },
            { label: 'Data Retention', sub: 'How long to keep deleted data', val: '30 days' },
          ].map((item, i) => (
            <div key={i} className={`flex flex-col sm:flex-row sm:items-center justify-between gap-2 ${i === 2 ? 'border-t border-[#1e2329]/50 pt-6' : ''}`}>
              <div className="flex flex-col">
                <span className="text-xs font-medium text-foreground">{item.label}</span>
                <span className="text-[10px] text-muted-foreground">{item.sub}</span>
              </div>
              <div className="relative sm:w-56">
                <select className="w-full appearance-none bg-[#161b22] border border-[#30363d] rounded-md pl-3 pr-8 py-1.5 text-xs text-foreground focus:outline-none focus:border-[#4b5563] text-right sm:text-left">
                  <option>{item.val}</option>
                </select>
                <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground pointer-events-none" />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Performance & Limits */}
      <div className="bg-[#12181f] border border-[#1e2329] rounded-xl flex flex-col overflow-hidden">
        <div className="p-5 border-b border-[#1e2329] flex items-center space-x-3 bg-[#12181f]">
          <div className="w-10 h-10 rounded-lg bg-[#3b82f6]/10 flex items-center justify-center flex-shrink-0 border border-[#3b82f6]/20">
            <BarChart2 className="w-5 h-5 text-[#3b82f6]" strokeWidth={1.5} />
          </div>
          <div className="flex flex-col">
            <h3 className="text-sm font-semibold text-foreground">Performance & Limits</h3>
            <p className="text-[11px] text-muted-foreground">Configure performance and rate limits</p>
          </div>
        </div>
        
        <div className="p-5 flex flex-col space-y-6 flex-1">
          {[
            { label: 'Rate Limit (Requests/Min)', sub: 'Maximum API requests per minute', val: '120', type: 'input' },
            { label: 'Concurrent Requests', sub: 'Maximum concurrent requests', val: '10', type: 'input' },
            { label: 'Cache TTL', sub: 'Response cache time to live', val: '1 hour', type: 'select' },
            { label: 'Max Concurrent Jobs', sub: 'Maximum background jobs', val: '5', type: 'input', border: true },
            { label: 'Memory Limit', sub: 'Memory limit for processing', val: '8 GB', type: 'select' },
          ].map((item, i) => (
            <div key={i} className={`flex flex-col sm:flex-row sm:items-center justify-between gap-2 ${item.border ? 'border-t border-[#1e2329]/50 pt-6' : ''}`}>
              <div className="flex flex-col">
                <span className="text-xs font-medium text-foreground">{item.label}</span>
                <span className="text-[10px] text-muted-foreground">{item.sub}</span>
              </div>
              <div className="relative sm:w-32">
                {item.type === 'input' ? (
                  <>
                    <input 
                      type="text" 
                      defaultValue={item.val}
                      className="w-full bg-[#161b22] border border-[#30363d] rounded-md pl-3 pr-8 py-1.5 text-xs text-foreground text-right focus:outline-none focus:border-[#4b5563]"
                    />
                    <ChevronsUpDown className="absolute right-2 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground opacity-50" />
                  </>
                ) : (
                  <>
                    <select className="w-full appearance-none bg-[#161b22] border border-[#30363d] rounded-md pl-3 pr-8 py-1.5 text-xs text-foreground focus:outline-none focus:border-[#4b5563] text-right sm:text-left">
                      <option>{item.val}</option>
                    </select>
                    <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground pointer-events-none" />
                  </>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

    </div>
  );
}

function GlobeIcon(props: any) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <circle cx="12" cy="12" r="10" />
      <path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20" />
      <path d="M2 12h20" />
    </svg>
  );
}
