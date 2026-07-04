"use client";

import React from 'react';
import { Wrench, Plug, Activity, Target, ArrowUp } from 'lucide-react';

interface Props {
  totalTools: number;
  activeTools: number;
  totalExecutions: number;
  successRate: number;
}

export function ToolsStatsRow({ totalTools, activeTools, totalExecutions, successRate }: Props) {
  const activePercent = totalTools > 0 ? ((activeTools / totalTools) * 100).toFixed(1) : '0';

  const StatCard = ({ title, value, subtext, subtextColor, icon: Icon, colorClass, iconBg }: any) => (
    <div className="flex-1 bg-[#12181f] border border-[#1e2329] rounded-xl p-4 hover:border-[#30363d] transition-colors flex flex-col justify-between min-h-[100px]">
      <div className="flex items-start justify-between">
        <div className="flex flex-col space-y-1">
          <span className="text-[10px] font-medium text-muted-foreground">{title}</span>
          <span className="text-xl font-bold text-foreground tracking-tight">{value}</span>
          <div className={`flex items-center text-[9px] mt-1 ${subtextColor}`}>
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
        value={totalTools}
        subtext={totalTools > 0 ? `${activeTools} active` : 'No tools yet'}
        subtextColor="text-muted-foreground"
        icon={Wrench}
        colorClass="text-[#10b981]"
        iconBg="bg-[#10b981]/10"
      />
      <StatCard
        title="Active Tools"
        value={activeTools}
        subtext={`${activePercent}% of total`}
        subtextColor="text-muted-foreground"
        icon={Plug}
        colorClass="text-[#3b82f6]"
        iconBg="bg-[#3b82f6]/10"
      />
      <StatCard
        title="Tool Executions"
        value={totalExecutions.toLocaleString()}
        subtext={totalExecutions > 0 ? 'Total recorded' : 'No executions yet'}
        subtextColor="text-muted-foreground"
        icon={Activity}
        colorClass="text-[#8b5cf6]"
        iconBg="bg-[#8b5cf6]/10"
      />
      <StatCard
        title="Success Rate"
        value={`${successRate.toFixed(1)}%`}
        subtext={totalExecutions > 0 ? 'Based on all executions' : 'No data yet'}
        subtextColor="text-muted-foreground"
        icon={Target}
        colorClass="text-yellow-500"
        iconBg="bg-yellow-500/10"
      />
    </div>
  );
}
