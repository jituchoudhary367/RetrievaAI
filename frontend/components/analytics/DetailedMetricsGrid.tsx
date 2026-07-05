"use client";

import React from 'react';
import { DetailedMetrics } from '../../lib/api/analytics';

export function DetailedMetricsGrid({ metrics }: { metrics: DetailedMetrics | null }) {
  if (!metrics) {
    return <div className="h-40 flex items-center justify-center text-muted-foreground">Loading metrics...</div>;
  }

  const { retrieval_analytics, query_pipeline, llm_usage, retrieval_quality, document_insights } = metrics;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
      {/* 1. Retrieval Analytics */}
      <div className="bg-[#12181f] border border-[#1e2329] rounded-xl p-5 flex flex-col">
        <h3 className="text-xs font-semibold text-foreground mb-4">Retrieval Analytics</h3>
        <div className="grid grid-cols-2 gap-y-4 gap-x-2">
          <div>
            <span className="text-[10px] text-muted-foreground block mb-1">Average Retrieved Chunks</span>
            <span className="text-lg font-semibold text-foreground">{retrieval_analytics.avg_retrieved_chunks}</span>
          </div>
          <div>
            <span className="text-[10px] text-muted-foreground block mb-1">Average Context Tokens</span>
            <span className="text-lg font-semibold text-foreground">{retrieval_analytics.avg_context_tokens.toLocaleString()}</span>
          </div>
          <div>
            <span className="text-[10px] text-muted-foreground block mb-1">Average Documents Used</span>
            <span className="text-lg font-semibold text-foreground">{retrieval_analytics.avg_documents_used}</span>
          </div>
          <div>
            <span className="text-[10px] text-muted-foreground block mb-1">Average Citation Count</span>
            <span className="text-lg font-semibold text-foreground">{retrieval_analytics.avg_citation_count}</span>
          </div>
          <div>
            <span className="text-[10px] text-muted-foreground block mb-1">Cache Hit Rate</span>
            <span className="text-lg font-semibold text-[#10b981]">{retrieval_analytics.cache_hit_rate}%</span>
          </div>
          <div>
            <span className="text-[10px] text-muted-foreground block mb-1">Web Search Triggered</span>
            <span className="text-lg font-semibold text-[#f97316]">{retrieval_analytics.web_search_triggered}%</span>
          </div>
        </div>
      </div>

      {/* 2. Query Pipeline Timeline */}
      <div className="bg-[#12181f] border border-[#1e2329] rounded-xl p-5 flex flex-col">
        <h3 className="text-xs font-semibold text-foreground mb-4">Average Pipeline</h3>
        <div className="flex flex-col space-y-3">
          <div className="flex items-center justify-between text-xs">
            <span className="text-muted-foreground w-16">Rewrite</span>
            <div className="flex-1 mx-3 h-2 bg-[#1e2329] rounded-full overflow-hidden">
              <div className="h-full bg-blue-500 rounded-full" style={{ width: `${Math.max(2, (query_pipeline.rewrite_ms / (query_pipeline.total_ms || 1)) * 100)}%` }} />
            </div>
            <span className="text-foreground w-12 text-right">{query_pipeline.rewrite_ms} ms</span>
          </div>
          <div className="flex items-center justify-between text-xs">
            <span className="text-muted-foreground w-16">Retrieve</span>
            <div className="flex-1 mx-3 h-2 bg-[#1e2329] rounded-full overflow-hidden">
              <div className="h-full bg-purple-500 rounded-full" style={{ width: `${Math.max(2, (query_pipeline.retrieve_ms / (query_pipeline.total_ms || 1)) * 100)}%` }} />
            </div>
            <span className="text-foreground w-12 text-right">{query_pipeline.retrieve_ms} ms</span>
          </div>
          <div className="flex items-center justify-between text-xs">
            <span className="text-muted-foreground w-16">Rerank</span>
            <div className="flex-1 mx-3 h-2 bg-[#1e2329] rounded-full overflow-hidden">
              <div className="h-full bg-orange-500 rounded-full" style={{ width: `${Math.max(2, (query_pipeline.rerank_ms / (query_pipeline.total_ms || 1)) * 100)}%` }} />
            </div>
            <span className="text-foreground w-12 text-right">{query_pipeline.rerank_ms} ms</span>
          </div>
          <div className="flex items-center justify-between text-xs">
            <span className="text-muted-foreground w-16">Generate</span>
            <div className="flex-1 mx-3 h-2 bg-[#1e2329] rounded-full overflow-hidden">
              <div className="h-full bg-green-500 rounded-full" style={{ width: `${Math.max(2, (query_pipeline.generate_ms / (query_pipeline.total_ms || 1)) * 100)}%` }} />
            </div>
            <span className="text-foreground w-12 text-right">{query_pipeline.generate_ms} ms</span>
          </div>
          <div className="flex items-center justify-between text-xs pt-2 border-t border-[#1e2329]">
            <span className="font-semibold text-foreground w-16">Total</span>
            <div className="flex-1 mx-3" />
            <span className="font-semibold text-foreground w-12 text-right">{query_pipeline.total_ms} ms</span>
          </div>
        </div>
      </div>

      {/* 3. LLM Usage */}
      <div className="bg-[#12181f] border border-[#1e2329] rounded-xl p-5 flex flex-col">
        <h3 className="text-xs font-semibold text-foreground mb-4">LLM Usage</h3>
        <div className="grid grid-cols-2 gap-y-4 gap-x-2">
          <div>
            <span className="text-[10px] text-muted-foreground block mb-1">Provider</span>
            <span className="text-sm font-semibold text-foreground">{llm_usage.provider}</span>
          </div>
          <div>
            <span className="text-[10px] text-muted-foreground block mb-1">Models Used</span>
            <span className="text-sm font-semibold text-foreground">{llm_usage.models_used}</span>
          </div>
          <div>
            <span className="text-[10px] text-muted-foreground block mb-1">Average Tokens</span>
            <span className="text-lg font-semibold text-foreground">{llm_usage.average_tokens.toLocaleString()}</span>
          </div>
          <div>
            <span className="text-[10px] text-muted-foreground block mb-1">Average Cost</span>
            <span className="text-lg font-semibold text-foreground">${llm_usage.average_cost_usd.toFixed(4)}</span>
          </div>
          <div>
            <span className="text-[10px] text-muted-foreground block mb-1">Prompt Tokens</span>
            <span className="text-sm font-medium text-muted-foreground">{llm_usage.prompt_tokens.toLocaleString()}</span>
          </div>
          <div>
            <span className="text-[10px] text-muted-foreground block mb-1">Completion Tokens</span>
            <span className="text-sm font-medium text-muted-foreground">{llm_usage.completion_tokens.toLocaleString()}</span>
          </div>
        </div>
      </div>

      {/* 4. Retrieval Quality */}
      <div className="bg-[#12181f] border border-[#1e2329] rounded-xl p-5 flex flex-col">
        <h3 className="text-xs font-semibold text-foreground mb-4">Retrieval Quality</h3>
        <div className="grid grid-cols-2 gap-y-4 gap-x-2">
          <div>
            <span className="text-[10px] text-muted-foreground block mb-1">Avg Retrieval Score</span>
            <span className="text-lg font-semibold text-foreground">{retrieval_quality.avg_retrieval_score}</span>
          </div>
          <div>
            <span className="text-[10px] text-muted-foreground block mb-1">Avg CrossEncoder Score</span>
            <span className="text-lg font-semibold text-foreground">{retrieval_quality.avg_crossencoder_score}</span>
          </div>
          <div>
            <span className="text-[10px] text-muted-foreground block mb-1">Low Confidence Answers</span>
            <span className="text-lg font-semibold text-yellow-500">{retrieval_quality.low_confidence_answers}%</span>
          </div>
          <div>
            <span className="text-[10px] text-muted-foreground block mb-1">Hallucination Prevented</span>
            <span className="text-lg font-semibold text-[#10b981]">{retrieval_quality.hallucination_prevented}</span>
          </div>
          <div>
            <span className="text-[10px] text-muted-foreground block mb-1">Need Web Trigger</span>
            <span className="text-lg font-semibold text-muted-foreground">{retrieval_quality.need_web_trigger}%</span>
          </div>
        </div>
      </div>

    </div>
  );
}
