"use client";

import React from 'react';
import { FileText, Database, HardDrive, Star } from 'lucide-react';

interface Props {
  totalDocuments: number;
  totalChunks: number;
  storageUsedBytes?: number;
  avgQualityScore?: number;
}

function formatBytes(bytes?: number): string {
  if (!bytes) return '—';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
}

function qualityLabel(score?: number): string {
  if (!score) return '—';
  if (score >= 0.9) return 'Excellent';
  if (score >= 0.7) return 'Good';
  return 'Fair';
}

function qualityColor(score?: number): string {
  if (!score) return 'text-muted-foreground';
  if (score >= 0.9) return 'text-yellow-500';
  if (score >= 0.7) return 'text-[#10b981]';
  return 'text-amber-500';
}

export function DocumentStatsRow({ totalDocuments, totalChunks, storageUsedBytes, avgQualityScore }: Props) {
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
        value={totalDocuments.toLocaleString()}
        subtext={totalDocuments === 0 ? 'No documents yet' : `${totalDocuments} document${totalDocuments !== 1 ? 's' : ''} indexed`}
        icon={FileText}
        colorClass="text-[#10b981]"
        iconBg="bg-[#10b981]/10"
      />
      <StatCard
        title="Total Chunks"
        value={totalChunks.toLocaleString()}
        subtext={totalChunks === 0 ? 'No chunks yet' : 'Vector embeddings stored'}
        icon={Database}
        colorClass="text-[#3b82f6]"
        iconBg="bg-[#3b82f6]/10"
      />
      <StatCard
        title="Storage Used"
        value={storageUsedBytes ? formatBytes(storageUsedBytes) : '—'}
        subtext="Blob storage"
        icon={HardDrive}
        colorClass="text-[#8b5cf6]"
        iconBg="bg-[#8b5cf6]/10"
      />
      <StatCard
        title="Avg. Quality Score"
        value={avgQualityScore ? avgQualityScore.toFixed(2) : '—'}
        subtext={<span className={qualityColor(avgQualityScore)}>{qualityLabel(avgQualityScore)}</span>}
        icon={Star}
        colorClass="text-yellow-500"
        iconBg="bg-yellow-500/10"
      />
    </div>
  );
}
