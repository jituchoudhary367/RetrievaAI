"use client";

import React from 'react';
import { Citation } from '../../lib/types/models';
import { MoreVertical, ArrowRight } from 'lucide-react';

export function SourcesPanel({ citations }: { citations: Citation[] }) {
  if (!citations || citations.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-32 text-muted-foreground text-sm p-4 text-center border-b border-[#30363d]">
        <p>No sources</p>
      </div>
    );
  }

  const getSourceIconColor = (index: number) => {
    const colors = [
      'bg-blue-600',
      'bg-blue-400',
      'bg-red-500',
      'bg-purple-600',
      'bg-blue-500'
    ];
    return colors[index % colors.length];
  };

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return 'text-[#10b981] border-[#10b981]/30 bg-[#122822]';
    if (score >= 0.5) return 'text-yellow-500 border-yellow-500/30 bg-yellow-500/10';
    return 'text-red-500 border-red-500/30 bg-red-500/10';
  };

  return (
    <div className="flex flex-col space-y-3 p-4 border-b border-[#30363d]">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-semibold text-foreground">Sources</h3>
        <span className="bg-[#21262d] text-muted-foreground text-[10px] px-2 py-0.5 rounded-full font-bold">
          {citations.length}
        </span>
      </div>
      
      <div className="space-y-3 max-h-[40vh] overflow-y-auto pr-1 scrollbar-thin">
        {citations.map((cit, index) => (
          <div key={cit.citationId} className="flex items-start justify-between group cursor-pointer hover:bg-muted/30 p-1.5 rounded-md transition-colors -mx-1.5">
            <div className="flex items-start space-x-3">
              {/* Number icon */}
              <div className={`w-5 h-5 rounded flex items-center justify-center text-white text-[10px] font-bold mt-0.5 ${getSourceIconColor(index)}`}>
                {index + 1}
              </div>
              <div className="flex flex-col">
                <span className="text-xs font-medium text-foreground truncate max-w-[160px]" title={cit.documentId}>
                  {cit.documentId}
                </span>
                <span className="text-[10px] text-muted-foreground mt-0.5">
                  {cit.pageNumber ? `Page ${cit.pageNumber}` : 'Section'} • {Math.round(cit.score * 100)}% relevant
                </span>
              </div>
            </div>
            
            <div className="flex items-center space-x-2">
              <span className={`text-[10px] px-1.5 py-0.5 rounded border font-medium ${getScoreColor(cit.score)}`}>
                {cit.score.toFixed(2)}
              </span>
              <button className="text-muted-foreground hover:text-foreground">
                <MoreVertical className="h-3.5 w-3.5" />
              </button>
            </div>
          </div>
        ))}
      </div>

      <button className="text-[10px] text-[#10b981] font-medium flex items-center justify-center mt-2 hover:underline">
        View all sources <ArrowRight className="ml-1 h-3 w-3" />
      </button>
    </div>
  );
}
