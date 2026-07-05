"use client";

import React from 'react';

interface Props {
  heatmap: { day: string; count: number }[];
}

export function ActivityHeatmap({ heatmap }: Props) {
  // Map days to ensure a consistent Mon-Sun order even if missing
  const daysOrder = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
  
  const maxCount = Math.max(...heatmap.map(d => d.count), 1); // Avoid div by 0

  return (
    <div className="bg-[#12181f] border border-[#1e2329] rounded-xl p-5 flex flex-col h-full">
      <h3 className="text-xs font-semibold text-foreground mb-4">Activity Heatmap</h3>
      <div className="flex flex-col justify-between flex-1 space-y-2">
        {daysOrder.map(day => {
          const entry = heatmap.find(h => h.day === day) || { day, count: 0 };
          const fillPercentage = Math.max(5, (entry.count / maxCount) * 100);
          
          return (
            <div key={day} className="flex items-center text-xs">
              <span className="text-muted-foreground w-8">{day}</span>
              <div className="flex-1 mx-2 flex items-center">
                <div 
                  className="h-3 bg-[#10b981] rounded-sm transition-all duration-500 opacity-80 hover:opacity-100" 
                  style={{ width: `${fillPercentage}%` }} 
                  title={`${entry.count} queries`}
                />
              </div>
              <span className="text-muted-foreground w-6 text-right opacity-0 group-hover:opacity-100">{entry.count}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
