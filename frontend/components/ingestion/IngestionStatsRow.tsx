"use client";

import React from 'react';
import { FileUp, Box, CheckCircle2, Clock } from 'lucide-react';

interface Props {
  totalJobs: number;
  totalChunks: number;
  successRate: number;  // 0–100
  avgProcessingMs?: number;
}

function formatDuration(ms?: number): string {
  if (!ms) return '—';
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  return `${Math.round(ms / 60000)}m`;
}

export function IngestionStatsRow({ totalJobs, totalChunks, successRate, avgProcessingMs }: Props) {
  const StatCard = ({ title, value, subtext, subtext2, icon: Icon, colorClass, iconBg }: any) => (
    <div className="flex-1 bg-[#12181f] border border-[#1e2329] rounded-xl p-4 hover:border-[#30363d] transition-colors flex items-center justify-between">
      <div className="flex flex-col space-y-1">
        <span className="text-[10px] font-semibold text-muted-foreground">{title}</span>
        <div className="flex items-baseline space-x-1">
          <span className="text-xl font-bold text-foreground tracking-tight">{value}</span>
          {subtext2 && <span className="text-[10px] text-muted-foreground">{subtext2}</span>}
        </div>
        <span className="text-[9px] font-medium text-muted-foreground pt-0.5">{subtext}</span>
      </div>
      <div className={`w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 ${iconBg} ${colorClass}`}>
        <Icon className="h-5 w-5" strokeWidth={1.5} />
      </div>
    </div>
  );

  return (
    <div className="flex flex-col sm:flex-row w-full gap-3">
      <StatCard
        title="Total Ingested Files"
        value={totalJobs.toLocaleString()}
        subtext={totalJobs === 0 ? 'No jobs yet' : 'All time'}
        icon={FileUp}
        colorClass="text-[#10b981]"
        iconBg="bg-[#10b981]/10"
      />
      <StatCard
        title="Total Chunks"
        value={totalChunks.toLocaleString()}
        subtext={totalChunks === 0 ? 'No chunks yet' : 'Across all documents'}
        icon={Box}
        colorClass="text-[#3b82f6]"
        iconBg="bg-[#3b82f6]/10"
      />
      <StatCard
        title="Success Rate"
        value={totalJobs > 0 ? `${successRate.toFixed(1)}%` : '—'}
        subtext={totalJobs > 0 ? 'Completed without error' : 'No jobs yet'}
        icon={CheckCircle2}
        colorClass="text-[#8b5cf6]"
        iconBg="bg-[#8b5cf6]/10"
      />
      <StatCard
        title="Avg. Processing Time"
        value={formatDuration(avgProcessingMs)}
        subtext="Per ingestion job"
        icon={Clock}
        colorClass="text-yellow-500"
        iconBg="bg-yellow-500/10"
      />
    </div>
  );
}
