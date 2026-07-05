"use client";

import React from 'react';
import { DetailedMetrics } from '../../lib/api/analytics';
import { ActivityHeatmap } from './ActivityHeatmap';
import { IntentDistribution } from './IntentDistribution';
import { RetrievalSources } from './RetrievalSources';
import { SlowQueries } from './SlowQueries';
import { FileText } from 'lucide-react';

export function AnalyticsBottomGrid({ metrics }: { metrics: DetailedMetrics | null }) {
  if (!metrics) return null;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-4 mb-4">
      {/* Popular Documents */}
      <div className="bg-[#12181f] border border-[#1e2329] rounded-xl p-5 flex flex-col h-full lg:col-span-1">
        <h3 className="text-xs font-semibold text-foreground mb-4">Top Documents</h3>
        <div className="flex flex-col space-y-3 flex-1">
          {metrics.popular_documents.length === 0 ? (
            <span className="text-xs text-muted-foreground">No documents queried yet.</span>
          ) : (
            metrics.popular_documents.map((doc, i) => (
              <div key={i} className="flex items-center justify-between group">
                <div className="flex items-center space-x-2 overflow-hidden pr-2">
                  <FileText className="w-3.5 h-3.5 text-muted-foreground flex-shrink-0" />
                  <span className="text-xs text-muted-foreground group-hover:text-foreground transition-colors truncate" title={doc.title}>
                    {doc.title}
                  </span>
                </div>
                <span className="text-[10px] font-medium text-muted-foreground ml-3 whitespace-nowrap bg-[#1e2329] px-1.5 py-0.5 rounded flex-shrink-0">
                  {doc.queries} q
                </span>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Activity Heatmap */}
      <div className="lg:col-span-2 flex flex-col h-full">
        <div className="h-full">
          <ActivityHeatmap heatmap={metrics.activity_heatmap} />
        </div>
      </div>

      {/* Search Intent Distribution */}
      <div className="lg:col-span-1">
        <IntentDistribution distribution={metrics.search_intent_distribution} />
      </div>

      {/* Retrieval Sources */}
      <div className="lg:col-span-1">
        <RetrievalSources sources={metrics.retrieval_sources} />
      </div>

      {/* Slow Queries */}
      <div className="lg:col-span-1">
        <SlowQueries queries={metrics.slow_queries} />
      </div>
    </div>
  );
}
