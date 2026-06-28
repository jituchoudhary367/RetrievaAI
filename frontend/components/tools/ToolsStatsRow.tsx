"use client";

import React from 'react';
import { Wrench, Plug, Activity, Target, ArrowUp, ArrowDown } from 'lucide-react';

export function ToolsStatsRow() {
  const StatCard = ({ title, value, subtext, subtextColor, subtextIcon: SubIcon, icon: Icon, colorClass, iconBg }: any) => (
    <div className="flex-1 bg-[#12181f] border border-[#1e2329] rounded-xl p-4 hover:border-[#30363d] transition-colors flex flex-col justify-between min-h-[100px]">
      <div className="flex items-start justify-between">
        <div className="flex flex-col space-y-1">
          <span className="text-[10px] font-medium text-muted-foreground">{title}</span>
          <span className="text-xl font-bold text-foreground tracking-tight">{value}</span>
          <div className={`flex items-center text-[9px] mt-1 ${subtextColor}`}>
            {SubIcon && <SubIcon className="w-3 h-3 mr-1" />}
            {subtext}
          </div>
        </div>
        <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${iconBg} ${colorClass}`}>
          <Icon className="h-4 w-4" strokeWidth={1.5} />
        </div>
      </div>
    </div>
  );

  return (
    <div className="flex flex-col sm:flex-row w-full gap-4">
      <StatCard 
        title="Total Tools" 
        value="18" 
        subtext="12% vs last 7 days"
        subtextColor="text-[#10b981]"
        subtextIcon={ArrowUp}
        icon={Wrench}
        colorClass="text-[#10b981]"
        iconBg="bg-[#10b981]/10"
      />
      <StatCard 
        title="Active Tools" 
        value="14" 
        subtext="77.8% of total"
        subtextColor="text-muted-foreground"
        icon={Plug}
        colorClass="text-[#3b82f6]"
        iconBg="bg-[#3b82f6]/10"
      />
      <StatCard 
        title="Tool Executions" 
        value="5,842" 
        subtext="28.4% vs last 7 days"
        subtextColor="text-[#10b981]"
        subtextIcon={ArrowUp}
        icon={Activity}
        colorClass="text-[#8b5cf6]"
        iconBg="bg-[#8b5cf6]/10"
      />
      <StatCard 
        title="Success Rate" 
        value="98.6%" 
        subtext="2.3% vs last 7 days"
        subtextColor="text-yellow-500"
        subtextIcon={ArrowUp}
        icon={Target}
        colorClass="text-yellow-500"
        iconBg="bg-yellow-500/10"
      />
    </div>
  );
}
