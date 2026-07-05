"use client";

import React from 'react';

interface Props {
  sources: { source: string; percentage: number }[];
}

export function RetrievalSources({ sources }: Props) {
  return (
    <div className="bg-[#12181f] border border-[#1e2329] rounded-xl p-5 flex flex-col h-full">
      <h3 className="text-xs font-semibold text-foreground mb-4">Retrieval Sources</h3>
      <div className="flex flex-col space-y-4 flex-1 justify-center">
        {sources.map((item, i) => {
          const colorClass = item.source === "Dense" ? "bg-[#8b5cf6]" : item.source === "Sparse" ? "bg-[#10b981]" : "bg-[#f97316]";
          return (
            <div key={i} className="flex flex-col space-y-1">
              <div className="flex items-center justify-between text-xs">
                <span className="text-muted-foreground">{item.source}</span>
                <span className="text-foreground">{item.percentage}%</span>
              </div>
              <div className="h-1.5 w-full bg-[#1e2329] rounded-full overflow-hidden">
                <div className={`h-full ${colorClass}`} style={{ width: `${item.percentage}%` }} />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
