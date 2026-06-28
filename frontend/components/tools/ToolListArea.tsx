"use client";

import React, { useState } from 'react';
import { Search, ChevronDown, LayoutGrid, List, Play, Settings, MoreVertical, Database, Globe, FileText, Code, DatabaseBackup, FileSignature, Link, Mail } from 'lucide-react';

export function ToolListArea() {
  
  const mockTools = [
    { id: 1, name: "Vector Search", desc: "Search across vector database", cat: "Retrieval", active: true, usage: 1824, sr: 99.2, ago: "2 min ago", icon: Database },
    { id: 2, name: "Web Search", desc: "Search real-time information from the web", cat: "Search", active: true, usage: 982, sr: 97.8, ago: "15 min ago", icon: Globe },
    { id: 3, name: "Document Summarizer", desc: "Summarize long documents or text", cat: "Processing", active: true, usage: 756, sr: 98.9, ago: "1 hr ago", icon: FileText },
    { id: 4, name: "Code Interpreter", desc: "Execute code and return results", cat: "Execution", active: true, usage: 612, sr: 99.1, ago: "2 hrs ago", icon: Code },
    { id: 5, name: "SQL Query", desc: "Query structured data sources using SQL", cat: "Data", active: true, usage: 432, sr: 96.5, ago: "3 hrs ago", icon: DatabaseBackup },
    { id: 6, name: "PDF Parser", desc: "Extract text and metadata from PDF files", cat: "Parser", active: true, usage: 389, sr: 99.4, ago: "5 hrs ago", icon: FileSignature },
    { id: 7, name: "Knowledge Graph Lookup", desc: "Retrieve related entities and relationships", cat: "Retrieval", active: false, usage: 128, sr: 97.2, ago: "1 day ago", icon: Link },
    { id: 8, name: "Email Sender", desc: "Send emails and notifications", cat: "Integration", active: false, usage: 64, sr: 100, ago: "2 days ago", icon: Mail },
  ];

  const getCatColor = (cat: string) => {
    switch (cat) {
      case 'Retrieval': return 'text-[#10b981] bg-[#10b981]/10 border-[#10b981]/20';
      case 'Search': return 'text-[#3b82f6] bg-[#3b82f6]/10 border-[#3b82f6]/20';
      case 'Processing': return 'text-[#8b5cf6] bg-[#8b5cf6]/10 border-[#8b5cf6]/20';
      case 'Execution': return 'text-yellow-500 bg-yellow-500/10 border-yellow-500/20';
      case 'Data': return 'text-[#06b6d4] bg-[#06b6d4]/10 border-[#06b6d4]/20';
      case 'Parser': return 'text-red-500 bg-red-500/10 border-red-500/20';
      case 'Integration': return 'text-[#3b82f6] bg-[#3b82f6]/10 border-[#3b82f6]/20';
      default: return 'text-muted-foreground bg-muted border-border';
    }
  };

  const UsageMiniChart = ({ colorClass }: { colorClass: string }) => {
    // Generate some random looking bars for the mock
    const heights = [3, 5, 8, 4, 10, 6, 9];
    return (
      <div className="flex items-end space-x-0.5 h-4 ml-3">
        {heights.map((h, i) => (
          <div key={i} className={`w-[2px] rounded-t-sm ${colorClass.replace('text-', 'bg-')}`} style={{ height: `${h * 10}%` }} />
        ))}
      </div>
    );
  };

  const SuccessRing = ({ sr, colorClass }: { sr: number, colorClass: string }) => (
    <div className="relative w-4 h-4 ml-3">
      <svg viewBox="0 0 24 24" className="w-full h-full transform -rotate-90">
        <circle cx="12" cy="12" r="10" fill="transparent" stroke="#30363d" strokeWidth="3" />
        <circle cx="12" cy="12" r="10" fill="transparent" className={colorClass.replace('text-', 'stroke-')} strokeWidth="3" strokeDasharray={`${(sr / 100) * 62.8} 62.8`} />
      </svg>
    </div>
  );

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
              className="w-full bg-[#161b22] border border-[#30363d] rounded-md pl-9 pr-3 py-1.5 text-xs text-foreground placeholder-muted-foreground focus:outline-none focus:border-[#4b5563] transition-colors"
            />
          </div>
          
          <div className="flex items-center bg-[#161b22] border border-[#30363d] rounded-md px-3 py-1.5 text-xs text-muted-foreground hover:text-foreground hover:border-[#4b5563] transition-colors cursor-pointer">
            <span>All Categories</span>
            <ChevronDown className="h-3 w-3 ml-2" />
          </div>

          <div className="flex items-center bg-[#161b22] border border-[#30363d] rounded-md px-3 py-1.5 text-xs text-muted-foreground hover:text-foreground hover:border-[#4b5563] transition-colors cursor-pointer">
            <span>All Status</span>
            <ChevronDown className="h-3 w-3 ml-2" />
          </div>
        </div>

        <div className="flex items-center space-x-4 w-full md:w-auto justify-end">
          <div className="flex items-center text-xs text-muted-foreground cursor-pointer hover:text-foreground">
            <span>Sort: <span className="text-foreground">Recently Used</span></span>
            <ChevronDown className="h-3 w-3 ml-1" />
          </div>
          
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
              <th className="px-6 py-4 font-medium w-32">Usage (7d)</th>
              <th className="px-6 py-4 font-medium w-32">Success Rate</th>
              <th className="px-6 py-4 font-medium w-28">Last Used</th>
              <th className="px-6 py-4 font-medium text-right w-32">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#1e2329]/50">
            {mockTools.map(tool => (
              <tr key={tool.id} className="hover:bg-[#1a212a] transition-colors group">
                
                <td className="px-6 py-4">
                  <div className="flex items-center space-x-3">
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${getCatColor(tool.cat)}`}>
                      <tool.icon className="h-4 w-4" strokeWidth={2} />
                    </div>
                    <div className="flex flex-col">
                      <span className="font-semibold text-foreground group-hover:text-primary transition-colors cursor-pointer">{tool.name}</span>
                      <span className="text-[10px] text-muted-foreground">{tool.desc}</span>
                    </div>
                  </div>
                </td>
                
                <td className="px-6 py-4">
                  <span className={`inline-flex items-center px-2 py-0.5 rounded text-[9px] border ${getCatColor(tool.cat)}`}>
                    {tool.cat}
                  </span>
                </td>
                
                <td className="px-6 py-4">
                  <span className={`inline-flex items-center px-2 py-0.5 rounded text-[9px] border ${tool.active ? 'text-[#10b981] bg-[#10b981]/10 border-[#10b981]/20' : 'text-muted-foreground bg-[#21262d] border-[#30363d]'}`}>
                    {tool.active ? 'Active' : 'Inactive'}
                  </span>
                </td>

                <td className="px-6 py-4">
                  <div className="flex items-center text-foreground font-medium">
                    {tool.usage.toLocaleString()}
                    <UsageMiniChart colorClass={getCatColor(tool.cat).split(' ')[0]} />
                  </div>
                </td>

                <td className="px-6 py-4">
                  <div className="flex items-center text-foreground font-medium">
                    {tool.sr}%
                    <SuccessRing sr={tool.sr} colorClass={getCatColor(tool.cat).split(' ')[0]} />
                  </div>
                </td>
                
                <td className="px-6 py-4 text-muted-foreground">
                  {tool.ago}
                </td>

                <td className="px-6 py-4 text-right">
                  <div className="flex items-center justify-end space-x-2 opacity-60 group-hover:opacity-100 transition-opacity">
                    <button className="p-1.5 rounded hover:bg-[#21262d] text-muted-foreground hover:text-foreground transition-colors border border-transparent hover:border-[#30363d]"><Play className="w-3 h-3" /></button>
                    <button className="p-1.5 rounded hover:bg-[#21262d] text-muted-foreground hover:text-foreground transition-colors border border-transparent hover:border-[#30363d]"><Settings className="w-3 h-3" /></button>
                    <button className="p-1.5 rounded hover:bg-[#21262d] text-muted-foreground hover:text-foreground transition-colors border border-transparent hover:border-[#30363d]"><MoreVertical className="w-3 h-3" /></button>
                  </div>
                </td>

              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="px-6 py-4 border-t border-[#1e2329] flex items-center justify-between text-[10px] text-muted-foreground mt-auto bg-[#12181f]">
        <span>Showing 1 to 8 of 18 tools</span>
        <div className="flex items-center space-x-1">
          <button className="w-6 h-6 rounded bg-[#21262d] text-[#10b981] flex items-center justify-center font-medium">1</button>
          <button className="w-6 h-6 rounded hover:bg-[#21262d] flex items-center justify-center transition-colors">2</button>
          <button className="w-6 h-6 rounded hover:bg-[#21262d] flex items-center justify-center transition-colors">3</button>
          <button className="w-6 h-6 rounded hover:bg-[#21262d] flex items-center justify-center transition-colors ml-2">{"<"}</button>
          <button className="w-6 h-6 rounded hover:bg-[#21262d] flex items-center justify-center transition-colors">{">"}</button>
        </div>
      </div>
      
    </div>
  );
}
