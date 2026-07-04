"use client";

import React, { useState } from 'react';
import { Calendar, ChevronRight } from 'lucide-react';

export function SearchFiltersPanel() {
  const [searchType, setSearchType] = useState('Hybrid Search');

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
        <button 
          onClick={() => setSearchType('Hybrid Search')}
          className="text-xs font-medium text-[#10b981] hover:text-[#059669] transition-colors"
        >
          Reset
        </button>
      </div>

      <FilterGroup 
        title="Search Type" 
        options={['Hybrid Search', 'Vector (Dense)', 'Keyword (BM25)']} 
        active={searchType} 
        onChange={setSearchType} 
      />

      {/* Dummy filters removed as requested */}
    </div>
  );
}
