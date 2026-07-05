"use client";

import React from 'react';
import { AlertCircle } from 'lucide-react';

interface Props {
  queries: { query: string; latency: string }[];
}

export function SlowQueries({ queries }: Props) {
  return (
    <div className="bg-[#12181f] border border-[#1e2329] rounded-xl p-5 flex flex-col h-full">
      <h3 className="text-xs font-semibold text-foreground mb-4">Slowest Queries</h3>
      <div className="flex flex-col space-y-3 flex-1">
        {queries.length === 0 ? (
          <span className="text-xs text-muted-foreground">No slow queries detected.</span>
        ) : (
          queries.map((item, i) => (
            <div key={i} className="flex items-center justify-between group">
              <div className="flex items-center space-x-2 overflow-hidden">
                <AlertCircle className="w-3.5 h-3.5 text-yellow-500 flex-shrink-0" />
                <span className="text-xs text-muted-foreground group-hover:text-foreground transition-colors truncate" title={item.query}>
                  {item.query}
                </span>
              </div>
              <span className="text-xs font-medium text-foreground ml-3 whitespace-nowrap">
                {item.latency}
              </span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
