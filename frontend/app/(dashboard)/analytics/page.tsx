"use client";

import React, { useState, useEffect, useCallback } from 'react';
import { TopBar } from '@/components/layout/TopBar';
import { AnalyticsStatsRow } from '@/components/analytics/AnalyticsStatsRow';
import { AnalyticsChartsGrid } from '@/components/analytics/AnalyticsChartsGrid';
import { AnalyticsMetricsRow } from '@/components/analytics/AnalyticsMetricsRow';
import { AnalyticsRightPanel } from '@/components/analytics/AnalyticsRightPanel';
import RequireAuth from '@/components/auth/RequireAuth';
import { analyticsApi } from '@/lib/api/analytics';

export default function AnalyticsPage() {
  const [querySeries, setQuerySeries] = useState<{ date: string; count: number }[]>([]);
  const [queryDistribution, setQueryDistribution] = useState<{ intent: string; count: number }[]>([]);
  const [topQueries, setTopQueries] = useState<{ query: string; intent: string; timestamp: string }[]>([]);
  const [retrievalMetrics, setRetrievalMetrics] = useState<any>(null);
  const [hasNoEvalData, setHasNoEvalData] = useState(false);

  const fetchAll = useCallback(async () => {
    // Fetch query time series (used for charts) — from query-distribution endpoint which returns daily counts
    try {
      const dist = await analyticsApi.getQueryDistribution(7);
      // Backend returns [{date, count}] — this is our time series
      if (Array.isArray(dist)) {
        setQuerySeries(dist.map((d: any) => ({ date: d.date || '', count: d.count || 0 })));
        // We don't have intent breakdown from this endpoint so leave distribution empty unless available
      }
    } catch (e) {
      console.warn('Query distribution fetch failed', e);
    }

    // Top queries
    try {
      const top = await analyticsApi.getTopQueries(10);
      if (Array.isArray(top)) {
        setTopQueries(top.map((q: any) => ({
          query: q.query || q.query_text || '',
          intent: q.intent || '',
          timestamp: q.timestamp || q.created_at || new Date().toISOString(),
        })));
      }
    } catch (e) {
      console.warn('Top queries fetch failed', e);
    }

    // Retrieval quality
    try {
      const quality = await analyticsApi.getRetrievalQuality();
      if (quality && quality.status === 'no_data') {
        setHasNoEvalData(true);
      } else if (quality && quality.metrics) {
        const m = quality.metrics;
        setRetrievalMetrics({
          top1Accuracy: m.top_1_accuracy ?? m.top1Accuracy,
          mrr: m.mrr,
          hitRate5: m.hit_rate_5 ?? m.hitRate5,
          ndcg10: m.ndcg_10 ?? m.ndcg10,
          evaluatedAt: quality.completed_at,
        });
      }
    } catch (e) {
      setHasNoEvalData(true);
      console.warn('Retrieval quality fetch failed', e);
    }
  }, []);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  return (
    <RequireAuth>
      <div className="flex flex-col h-full bg-background relative overflow-hidden">
        <TopBar title="Analytics" />
        <div className="flex flex-1 overflow-hidden">
          <div className="flex-1 flex flex-col min-w-0 border-r border-border bg-background p-4 overflow-y-auto space-y-4">
            {/* Stats row already fetches internally */}
            <AnalyticsStatsRow />
            <AnalyticsChartsGrid
              querySeries={querySeries}
              queryDistribution={queryDistribution}
            />
            <AnalyticsMetricsRow
              retrievalMetrics={retrievalMetrics}
              hasNoData={hasNoEvalData}
            />
          </div>
          <div className="w-80 flex-shrink-0 flex flex-col bg-muted/10 overflow-y-auto hidden lg:flex">
            <AnalyticsRightPanel topQueries={topQueries} />
          </div>
        </div>
      </div>
    </RequireAuth>
  );
}
