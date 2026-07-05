"use client";

import React from 'react';

interface TopQuery {
  query: string;
  intent: string;
  timestamp: string;
}

interface Props {
  topQueries: TopQuery[];
}

export function AnalyticsRightPanel({ topQueries }: Props) {
  const getRelTime = (iso: string) => {
    const diff = Date.now() - new Date(iso).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'Just now';
    if (mins < 60) return `${mins}m ago`;
    return `${Math.floor(mins / 60)}h ago`;
  };

  return (
    <div className="flex-1 flex flex-col p-6 space-y-6">
      
      {/* Top Queries */}
      <div className="flex flex-col space-y-4">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-foreground">Recent Queries</span>
        </div>
        
        <div className="flex flex-col space-y-4 text-[11px]">
          {topQueries.length === 0 ? (
            <span className="text-muted-foreground">No queries yet</span>
          ) : (
            topQueries.slice(0, 10).map((item, i) => (
              <div key={i} className="flex flex-col space-y-2 p-3 bg-[#12181f] rounded-lg border border-[#1e2329]">
                <div className="flex items-center space-x-1.5">
                  <div className="w-2 h-2 rounded-full bg-[#10b981]" />
                  <span className="font-semibold text-muted-foreground">Success</span>
                  <span className="text-muted-foreground/50 mx-1">•</span>
                  <span className="text-muted-foreground">{getRelTime(item.timestamp)}</span>
                </div>
                
                <span className="font-medium text-foreground line-clamp-2" title={item.query}>
                  {item.query}
                </span>
                
                <div className="flex items-center space-x-3 text-muted-foreground pt-1 border-t border-[#1e2329]/50 mt-1">
                  <span>324 ms</span>
                  <span className="text-muted-foreground/50">•</span>
                  <span>Retrieved 8 chunks</span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

    </div>
  );
}
