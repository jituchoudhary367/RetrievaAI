"use client";

import React from 'react';
import { ArrowUp, ArrowDown } from 'lucide-react';

interface RetrievalMetrics {
  top1Accuracy?: number;
  mrr?: number;
  hitRate5?: number;
  ndcg10?: number;
  evaluatedAt?: string;
}

interface Props {
  retrievalMetrics: RetrievalMetrics | null;
  hasNoData: boolean;
}

export function AnalyticsMetricsRow({ retrievalMetrics, hasNoData }: Props) {
  const MetricItem = ({ label, value }: { label: string; value: string | React.ReactNode }) => (
    <div className="flex flex-col space-y-1">
      <div className="flex items-center space-x-1">
        <span className="text-[10px] text-muted-foreground">{label}</span>
      </div>
      <span className="text-xl font-bold text-foreground">{value}</span>
    </div>
  );

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      
      {/* Retrieval Performance — real data from last EvalRun */}
      <div className="bg-[#12181f] border border-[#1e2329] rounded-xl p-5 flex flex-col justify-between min-h-[140px]">
        <div className="flex flex-col space-y-1 mb-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-foreground">Retrieval Performance</span>
            {retrievalMetrics?.evaluatedAt && (
              <span className="text-[9px] text-muted-foreground">
                as of {new Date(retrievalMetrics.evaluatedAt).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
              </span>
            )}
          </div>
          <span className="text-[10px] text-muted-foreground">Retrieval quality metrics</span>
        </div>
        
        {hasNoData ? (
          <div className="flex items-center space-x-6">
            {['Top 1 Accuracy', 'MRR', 'Hit Rate@5', 'NDCG@10'].map(label => (
              <MetricItem key={label} label={label} value="—" />
            ))}
            <p className="text-[9px] text-muted-foreground col-span-4 mt-1">No eval run yet</p>
          </div>
        ) : (
          <div className="flex items-center justify-between">
            <MetricItem
              label="Top 1 Accuracy"
              value={retrievalMetrics?.top1Accuracy !== undefined ? `${(retrievalMetrics.top1Accuracy * 100).toFixed(1)}%` : '—'}
            />
            <MetricItem
              label="MRR"
              value={retrievalMetrics?.mrr !== undefined ? retrievalMetrics.mrr.toFixed(2) : '—'}
            />
            <MetricItem
              label="Hit Rate@5"
              value={retrievalMetrics?.hitRate5 !== undefined ? `${(retrievalMetrics.hitRate5 * 100).toFixed(1)}%` : '—'}
            />
            <MetricItem
              label="NDCG@10"
              value={retrievalMetrics?.ndcg10 !== undefined ? retrievalMetrics.ndcg10.toFixed(2) : '—'}
            />
          </div>
        )}
      </div>

      {/* User Engagement — shows zeros until we have backend support */}
      <div className="bg-[#12181f] border border-[#1e2329] rounded-xl p-5 flex flex-col justify-between min-h-[140px]">
        <div className="flex flex-col space-y-1 mb-4">
          <span className="text-xs font-semibold text-foreground">User Engagement</span>
          <span className="text-[10px] text-muted-foreground">User interaction metrics</span>
        </div>
        <div className="flex items-center justify-between">
          <MetricItem label="Active Users" value="—" />
          <MetricItem label="New Users" value="—" />
          <MetricItem label="Conversations" value="—" />
          <MetricItem label="Avg. Turns" value="—" />
        </div>
      </div>

    </div>
  );
}
