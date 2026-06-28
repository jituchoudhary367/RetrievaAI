"use client";

import React from 'react';

export function SearchAnalyticsPanel() {
  const StatRow = ({ label, value, change, color }: { label: string, value: string, change: string, color: string }) => (
    <div className="flex items-center justify-between text-xs py-1.5">
      <span className="text-muted-foreground">{label}</span>
      <div className="flex items-center space-x-4">
        <span className="font-medium text-foreground">{value}</span>
        <span className={`text-[10px] font-medium min-w-[32px] text-right ${color}`}>{change}</span>
      </div>
    </div>
  );

  return (
    <div className="flex flex-col p-6">
      <h3 className="text-sm font-semibold text-foreground mb-6">Search Analytics</h3>
      
      {/* Mock Chart */}
      <div className="w-full h-24 mb-8 flex items-end justify-between relative">
        {/* Subtle grid lines */}
        <div className="absolute inset-0 flex flex-col justify-between pointer-events-none opacity-20">
          <div className="border-b border-[#30363d] w-full" />
          <div className="border-b border-[#30363d] w-full" />
          <div className="border-b border-[#30363d] w-full" />
          <div className="border-b border-[#30363d] w-full" />
        </div>
        
        {/* Sparkline SVG */}
        <svg viewBox="0 0 100 40" preserveAspectRatio="none" className="absolute inset-0 w-full h-full overflow-visible">
          <path
            d="M0,20 L10,15 L20,25 L30,5 L40,18 L50,15 L60,35 L70,30 L80,10 L90,20 L100,5"
            fill="none"
            stroke="#10b981"
            strokeWidth="1.5"
            vectorEffect="non-scaling-stroke"
          />
          {/* Dots on the line */}
          <circle cx="0" cy="20" r="1.5" fill="#10b981" />
          <circle cx="10" cy="15" r="1.5" fill="#10b981" />
          <circle cx="20" cy="25" r="1.5" fill="#10b981" />
          <circle cx="30" cy="5" r="1.5" fill="#10b981" />
          <circle cx="40" cy="18" r="1.5" fill="#10b981" />
          <circle cx="50" cy="15" r="1.5" fill="#10b981" />
          <circle cx="60" cy="35" r="1.5" fill="#10b981" />
          <circle cx="70" cy="30" r="1.5" fill="#10b981" />
          <circle cx="80" cy="10" r="1.5" fill="#10b981" />
          <circle cx="90" cy="20" r="1.5" fill="#10b981" />
          <circle cx="100" cy="5" r="1.5" fill="#10b981" />
        </svg>
      </div>

      {/* Stats Grid */}
      <div className="flex flex-col space-y-3">
        <StatRow label="Total Searches" value="1,248" change="+18%" color="text-[#10b981]" />
        <StatRow label="Avg. Response Time" value="0.42s" change="-12%" color="text-yellow-500" />
        <StatRow label="Results per Search" value="98" change="+5%" color="text-[#10b981]" />
        <StatRow label="Click Through Rate" value="76%" change="+8%" color="text-[#10b981]" />
      </div>

    </div>
  );
}
