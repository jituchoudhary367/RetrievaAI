"use client";

import React from 'react';

interface Props {
  distribution: { intent: string; count: number }[];
}

export function IntentDistribution({ distribution }: Props) {
  const total = distribution.reduce((sum, item) => sum + item.count, 0);
  // Sort descending by count
  const sorted = [...distribution].sort((a, b) => b.count - a.count).slice(0, 5);

  return (
    <div className="bg-[#12181f] border border-[#1e2329] rounded-xl p-5 flex flex-col h-full">
      <h3 className="text-xs font-semibold text-foreground mb-4">Search Intent Distribution</h3>
      <div className="flex flex-col space-y-4 flex-1">
        {sorted.length === 0 ? (
          <span className="text-xs text-muted-foreground">No data available</span>
        ) : (
          sorted.map((item, i) => {
            const percentage = total > 0 ? Math.round((item.count / total) * 100) : 0;
            return (
              <div key={i} className="flex flex-col space-y-1">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-muted-foreground capitalize">{item.intent}</span>
                  <span className="text-foreground">{percentage}%</span>
                </div>
                <div className="h-1.5 w-full bg-[#1e2329] rounded-full overflow-hidden">
                  <div className="h-full bg-[#3b82f6]" style={{ width: `${percentage}%` }} />
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
