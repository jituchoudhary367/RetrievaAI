"use client";

import React, { useState, useEffect, useCallback } from 'react';
import { TopBar } from '@/components/layout/TopBar';
import { AnalyticsStatsRow } from '@/components/analytics/AnalyticsStatsRow';
import { AnalyticsRightPanel } from '@/components/analytics/AnalyticsRightPanel';
import { DetailedMetricsGrid } from '@/components/analytics/DetailedMetricsGrid';
import { AnalyticsBottomGrid } from '@/components/analytics/AnalyticsBottomGrid';
import RequireAuth from '@/components/auth/RequireAuth';
import { analyticsApi, DetailedMetrics } from '@/lib/api/analytics';

export default function AnalyticsPage() {
  const [detailedMetrics, setDetailedMetrics] = useState<DetailedMetrics | null>(null);
  const [topQueries, setTopQueries] = useState<{ query: string; intent: string; timestamp: string }[]>([]);

  const fetchAll = useCallback(async () => {
    // Detailed Metrics
    try {
      const data = await analyticsApi.getDetailedMetrics(7);
      setDetailedMetrics(data);
    } catch (e) {
      console.warn('Detailed metrics fetch failed', e);
    }

    // Top queries for right panel
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
  }, []);

  useEffect(() => {
    fetchAll();
    const interval = setInterval(fetchAll, 5000);
    return () => clearInterval(interval);
  }, [fetchAll]);

  return (
    <RequireAuth>
      <div className="flex flex-col h-full bg-background relative overflow-hidden">
        <TopBar title="Analytics" />
        <div className="flex flex-1 overflow-hidden">
          <div className="flex-1 flex flex-col min-w-0 border-r border-border bg-background p-4 overflow-y-auto">
            {/* KPI Row */}
            <AnalyticsStatsRow />
            
            {/* New Detailed Metrics Grid */}
            <DetailedMetricsGrid metrics={detailedMetrics} />
            
            {/* Bottom Grid for Heatmap, Intents, Sources, etc */}
            <AnalyticsBottomGrid metrics={detailedMetrics} />
          </div>
          <div className="w-80 flex-shrink-0 flex flex-col bg-muted/10 overflow-y-auto hidden lg:flex">
            <AnalyticsRightPanel topQueries={topQueries} />
          </div>
        </div>
      </div>
    </RequireAuth>
  );
}
