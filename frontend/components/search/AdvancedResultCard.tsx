"use client";

import React from 'react';
import { MoreVertical, FileText, Code } from 'lucide-react';

export function AdvancedResultCard({ result, index }: { result: any, index: string }) {
  const getIcon = (type: string) => {
    switch (type) {
      case 'pdf': 
        return <div className="w-6 h-6 rounded bg-red-500/20 text-red-500 flex items-center justify-center flex-shrink-0"><FileText className="h-3.5 w-3.5" /></div>;
      case 'md': 
        return <div className="w-6 h-6 rounded bg-purple-500/20 text-purple-400 flex items-center justify-center flex-shrink-0 font-bold text-[10px]">M↓</div>;
      case 'code': 
        return <div className="w-6 h-6 rounded bg-green-500/20 text-green-500 flex items-center justify-center flex-shrink-0"><Code className="h-3.5 w-3.5" /></div>;
      default:
        return <div className="w-6 h-6 rounded bg-blue-500/20 text-blue-400 flex items-center justify-center flex-shrink-0"><FileText className="h-3.5 w-3.5" /></div>;
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return 'text-[#10b981] border-[#10b981]/30 bg-[#122822]';
    if (score >= 0.5) return 'text-yellow-500 border-yellow-500/30 bg-yellow-500/10';
    return 'text-red-500 border-red-500/30 bg-red-500/10';
  };

  return (
    <div className="flex flex-col bg-[#12181f] border border-[#1e2329] rounded-xl p-5 hover:border-[#30363d] transition-colors group">
      
      {/* Header Row */}
      <div className="flex items-start justify-between w-full">
        <div className="flex items-start space-x-3">
          {/* Number Badge */}
          <div className="w-6 h-6 rounded bg-blue-600 flex items-center justify-center text-white text-[10px] font-bold mt-0.5">
            {index}
          </div>
          {/* File Icon */}
          <div className="mt-0.5">
            {getIcon(result.type)}
          </div>
          {/* Title & Subtitle */}
          <div className="flex flex-col space-y-1">
            <h3 className="text-sm font-semibold text-foreground group-hover:text-[#10b981] transition-colors cursor-pointer">
              {result.title}
            </h3>
            <span className="text-[10px] text-muted-foreground font-medium">
              {result.subtitle}
            </span>
          </div>
        </div>

        {/* Score & Actions */}
        <div className="flex items-center space-x-3 mt-0.5">
          <div className={`text-[10px] font-bold px-2 py-0.5 rounded border ${getScoreColor(result.score)}`}>
            {result.score.toFixed(2)}
          </div>
          <button className="text-muted-foreground hover:text-foreground transition-colors">
            <MoreVertical className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Snippet */}
      <div className="mt-4 pl-[3.25rem] pr-2">
        <p 
          className="text-xs text-foreground/80 leading-relaxed font-sans"
          dangerouslySetInnerHTML={{ __html: result.snippet }}
        />
      </div>

      {/* Footer / Matches */}
      <div className="mt-3 pl-[3.25rem]">
        <span className="text-[10px] text-muted-foreground">
          <span className="font-medium text-foreground/70">Matches:</span> {result.matches}
        </span>
      </div>

    </div>
  );
}
