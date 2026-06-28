"use client";

import React from 'react';
import { Search, X, BarChart } from 'lucide-react';

export function SearchInputArea({ query, setQuery }: { query: string, setQuery: (q: string) => void }) {
  const tabs = ["All Results", "Documents", "Code", "Web", "Knowledge Base"];

  return (
    <div className="flex flex-col w-full">
      {/* Search Bar */}
      <div className="relative flex items-center w-full bg-[#12181f] border border-[#1e2329] rounded-lg p-1.5 shadow-sm focus-within:border-[#10b981] transition-colors">
        <div className="pl-3 pr-2 text-muted-foreground">
          <Search className="h-5 w-5" />
        </div>
        <input 
          type="text" 
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="flex-1 bg-transparent border-none outline-none text-foreground text-base placeholder-muted-foreground px-2 py-2"
          placeholder="Search..."
        />
        {query && (
          <button 
            onClick={() => setQuery("")}
            className="p-1 mr-2 text-muted-foreground hover:text-foreground transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        )}
        <button className="bg-[#122822] hover:bg-[#1a382f] border border-[#10b981]/30 text-[#10b981] px-6 py-2 rounded-md font-medium text-sm transition-colors flex items-center">
          <Search className="h-4 w-4 mr-2" />
          Search
        </button>
      </div>

      {/* Tabs */}
      <div className="flex items-center space-x-6 mt-6 border-b border-[#30363d] px-1">
        {tabs.map((tab, i) => (
          <button 
            key={i}
            className={`pb-3 text-sm font-medium transition-colors border-b-2 ${
              i === 0 
                ? 'border-[#10b981] text-[#e6edf3]' 
                : 'border-transparent text-muted-foreground hover:text-foreground hover:border-[#4b5563]'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Info Line */}
      <div className="flex items-center justify-between mt-6 px-1">
        <div className="flex items-center text-xs text-muted-foreground">
          <span>About 128 results (0.42s)</span>
          <BarChart className="ml-2 h-3.5 w-3.5" />
        </div>
        <div className="flex items-center text-xs text-muted-foreground space-x-1 cursor-pointer hover:text-foreground">
          <span>Sort by:</span>
          <span className="font-medium text-foreground">Relevance</span>
          <span className="ml-1 text-[10px]">⌄</span>
        </div>
      </div>
    </div>
  );
}
