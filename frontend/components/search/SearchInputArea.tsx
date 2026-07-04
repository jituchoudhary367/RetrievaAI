"use client";

import React from 'react';
import { Search, X, BarChart } from 'lucide-react';

export function SearchInputArea({ 
  query, 
  setQuery, 
  onSearch, 
  isLoading,
  activeTab = "All Results",
  onTabChange
}: { 
  query: string, 
  setQuery: (q: string) => void,
  onSearch?: () => void,
  isLoading?: boolean,
  activeTab?: string,
  onTabChange?: (tab: string) => void
}) {
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
          onKeyDown={(e) => e.key === 'Enter' && onSearch && onSearch()}
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
        <button 
          onClick={onSearch}
          disabled={isLoading}
          className="bg-[#122822] hover:bg-[#1a382f] border border-[#10b981]/30 text-[#10b981] px-6 py-2 rounded-md font-medium text-sm transition-colors flex items-center disabled:opacity-50"
        >
          <Search className="h-4 w-4 mr-2" />
          {isLoading ? 'Searching...' : 'Search'}
        </button>
      </div>

      {/* Tabs */}
      <div className="flex items-center space-x-6 mt-6 border-b border-[#30363d] px-1">
        {tabs.map((tab, i) => (
          <button 
            key={i}
            onClick={() => onTabChange && onTabChange(tab)}
            className={`pb-3 text-sm font-medium transition-colors border-b-2 ${
              activeTab === tab 
                ? 'border-[#10b981] text-[#e6edf3]' 
                : 'border-transparent text-muted-foreground hover:text-foreground hover:border-[#4b5563]'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Info Line Removed */}
    </div>
  );
}
