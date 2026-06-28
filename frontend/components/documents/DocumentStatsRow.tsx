"use client";

import React from 'react';
import { FileText, Database, HardDrive, Star } from 'lucide-react';

export function DocumentStatsRow() {
  const StatCard = ({ title, value, subtext, icon: Icon, colorClass, iconBg }: any) => (
    <div className="flex-1 bg-[#12181f] border border-[#1e2329] rounded-xl p-5 hover:border-[#30363d] transition-colors flex items-center justify-between">
      <div className="flex flex-col space-y-1">
        <span className="text-xs font-medium text-muted-foreground">{title}</span>
        <span className="text-2xl font-bold text-foreground tracking-tight">{value}</span>
        <span className="text-[10px] font-medium text-muted-foreground pt-1">{subtext}</span>
      </div>
      <div className={`w-12 h-12 rounded-lg flex items-center justify-center flex-shrink-0 ${iconBg} ${colorClass}`}>
        <Icon className="h-6 w-6" strokeWidth={1.5} />
      </div>
    </div>
  );

  return (
    <div className="flex flex-col sm:flex-row w-full gap-4">
      <StatCard 
        title="Total Documents" 
        value="1,248" 
        subtext={<><span className="text-[#10b981]">+24</span> this week</>}
        icon={FileText}
        colorClass="text-[#10b981]"
        iconBg="bg-[#10b981]/10"
      />
      <StatCard 
        title="Total Chunks" 
        value="32,654" 
        subtext={<><span className="text-[#3b82f6]">+512</span> this week</>}
        icon={Database}
        colorClass="text-[#3b82f6]"
        iconBg="bg-[#3b82f6]/10"
      />
      <StatCard 
        title="Storage Used" 
        value="18.7 GB" 
        subtext="28% of 100 GB"
        icon={HardDrive}
        colorClass="text-[#8b5cf6]"
        iconBg="bg-[#8b5cf6]/10"
      />
      <StatCard 
        title="Avg. Quality Score" 
        value="0.92" 
        subtext={<span className="text-yellow-500">Excellent</span>}
        icon={Star}
        colorClass="text-yellow-500"
        iconBg="bg-yellow-500/10"
      />
    </div>
  );
}
