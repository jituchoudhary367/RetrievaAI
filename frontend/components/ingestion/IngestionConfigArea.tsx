"use client";

import React from 'react';
import { Settings, Play, ChevronDown } from 'lucide-react';

export function IngestionConfigArea() {
  const SelectField = ({ label, value }: { label: string, value: string }) => (
    <div className="flex flex-col space-y-2 w-full max-w-[180px]">
      <span className="text-[10px] text-muted-foreground">{label}</span>
      <div className="flex items-center justify-between w-full bg-transparent border border-[#30363d] rounded-md px-3 py-2 cursor-not-allowed group">
        <span className="text-xs text-foreground">{value}</span>
        <ChevronDown className="h-3 w-3 text-muted-foreground group-hover:text-foreground transition-colors" />
      </div>
    </div>
  );

  return (
    <div className="flex flex-col space-y-4">
      <div className="flex items-center space-x-2 text-xs font-semibold text-muted-foreground cursor-pointer hover:text-foreground transition-colors w-fit">
        <Settings className="w-4 h-4" />
        <span>Advanced Options</span>
        <ChevronDown className="w-3.5 h-3.5" />
      </div>
      
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div className="flex flex-wrap items-end gap-6">
          <SelectField label="Chunk Size" value="1024 tokens" />
          <SelectField label="Chunk Overlap" value="200 tokens" />
          <SelectField label="Embedding Model" value="bge-large-en-v1.5" />
          <SelectField label="Parser" value="Auto Detect" />
        </div>
        
        <button className="flex items-center justify-center bg-[#10b981] hover:bg-[#059669] text-background px-6 py-2.5 rounded-md font-semibold text-xs transition-colors flex-shrink-0">
          <Play className="w-4 h-4 mr-2" fill="currentColor" />
          Start Ingestion
        </button>
      </div>
    </div>
  );
}
