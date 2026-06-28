"use client";

import React from 'react';
import { ResponseMetadata, MetadataFilter } from '../../lib/types/models';

export function RetrievalDetailsPanel({ 
  metadata, 
  filters 
}: { 
  metadata?: ResponseMetadata; 
  filters?: MetadataFilter[]; 
}) {
  return (
    <div className="flex flex-col space-y-3 p-4 border-b border-[#30363d]">
      <h3 className="text-sm font-semibold text-foreground mb-2">Retrieval Details</h3>
      
      <div className="space-y-2">
        <div className="flex items-center justify-between text-xs">
          <span className="text-muted-foreground">Search Type</span>
          <span className="text-foreground">Hybrid (Dense + BM25 + RRF)</span>
        </div>

        <div className="flex items-center justify-between text-xs">
          <span className="text-muted-foreground">Total Retrieved</span>
          <span className="text-foreground">32 documents</span>
        </div>

        <div className="flex items-center justify-between text-xs">
          <span className="text-muted-foreground">Reranked</span>
          <span className="text-foreground">10 documents</span>
        </div>

        <div className="flex items-center justify-between text-xs">
          <span className="text-muted-foreground">Top K</span>
          <span className="text-foreground">5</span>
        </div>

        <div className="flex flex-col text-xs">
          <div className="flex justify-between items-start">
            <span className="text-muted-foreground">Filters</span>
            <div className="flex flex-col items-end">
              {!filters || filters.length === 0 ? (
                <span className="text-foreground">None</span>
              ) : (
                filters.map((f, i) => (
                  <span key={i} className="text-foreground">
                    {f.field} {f.operator} {String(f.value)}
                  </span>
                ))
              )}
            </div>
          </div>
        </div>

        <div className="flex items-center justify-between text-xs">
          <span className="text-muted-foreground">Time Taken</span>
          <span className="text-foreground">
            {metadata?.totalLatencyMs !== undefined ? `${metadata.totalLatencyMs} ms` : '--'}
          </span>
        </div>
      </div>
    </div>
  );
}
