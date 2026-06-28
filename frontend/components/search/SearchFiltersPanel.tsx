"use client";

import React, { useState } from 'react';
import { Calendar, ChevronRight } from 'lucide-react';

export function SearchFiltersPanel() {
  const [searchType, setSearchType] = useState('Hybrid Search');
  const [fileType, setFileType] = useState('All Types');
  const [source, setSource] = useState('All Sources');

  const FilterGroup = ({ title, options, active, onChange }: { title: string, options: string[], active: string, onChange: (val: string) => void }) => (
    <div className="flex flex-col space-y-3 mb-6">
      <span className="text-xs font-semibold text-muted-foreground">{title}</span>
      <div className="flex flex-wrap gap-2">
        {options.map((opt) => (
          <button
            key={opt}
            onClick={() => onChange(opt)}
            className={`text-[10px] font-medium px-3 py-1.5 rounded-md transition-colors border ${
              active === opt
                ? 'bg-[#122822] border-[#10b981]/30 text-[#10b981]'
                : 'bg-transparent border-[#30363d] text-muted-foreground hover:text-foreground hover:border-[#4b5563]'
            }`}
          >
            {opt}
          </button>
        ))}
      </div>
    </div>
  );

  return (
    <div className="flex flex-col p-6 border-b border-[#30363d]">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-sm font-semibold text-foreground">Search Filters</h3>
        <button className="text-xs font-medium text-[#10b981] hover:text-[#059669] transition-colors">
          Reset
        </button>
      </div>

      <FilterGroup 
        title="Search Type" 
        options={['Hybrid Search', 'Vector (Dense)', 'Keyword (BM25)']} 
        active={searchType} 
        onChange={setSearchType} 
      />

      <FilterGroup 
        title="File Type" 
        options={['All Types', 'PDF', 'Markdown', 'Code', 'Web']} 
        active={fileType} 
        onChange={setFileType} 
      />

      <div className="flex flex-col space-y-3 mb-6">
        <span className="text-xs font-semibold text-muted-foreground">Date Range</span>
        <div className="flex flex-col space-y-2">
          <div className="flex items-center justify-between bg-transparent border border-[#30363d] rounded-md px-3 py-2 cursor-not-allowed group">
            <span className="text-xs text-[#10b981]">Any Time</span>
            <Calendar className="h-3.5 w-3.5 text-muted-foreground group-hover:text-foreground transition-colors" />
          </div>
          <div className="flex items-center justify-between bg-transparent border border-[#30363d] rounded-md px-3 py-2 cursor-not-allowed group opacity-50">
            <span className="text-xs text-muted-foreground">Custom Range</span>
            <Calendar className="h-3.5 w-3.5 text-muted-foreground group-hover:text-foreground transition-colors" />
          </div>
        </div>
      </div>

      <FilterGroup 
        title="Source" 
        options={['All Sources', 'Knowledge Base', 'Web', 'Code Repositories']} 
        active={source} 
        onChange={setSource} 
      />

      <div className="flex items-center justify-between p-3 bg-transparent border border-[#30363d] rounded-lg cursor-not-allowed mt-2 hover:bg-muted/10 transition-colors">
        <span className="text-xs text-muted-foreground font-medium">Advanced Filters</span>
        <ChevronRight className="h-4 w-4 text-muted-foreground" />
      </div>

    </div>
  );
}
