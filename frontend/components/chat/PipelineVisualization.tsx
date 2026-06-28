"use client";

import React from 'react';
import { ResponseMetadata } from '../../lib/types/models';
import { User, Search, FileText, MessageSquare, Sparkles, CheckCircle2, ExternalLink } from 'lucide-react';

export function PipelineVisualization({ metadata }: { metadata?: ResponseMetadata }) {
  if (!metadata) return null;

  const Node = ({ icon: Icon, title, subtitle, colorClass }: { icon: any, title: string, subtitle?: string, colorClass: string }) => (
    <div className="flex flex-col items-center justify-center flex-1 min-w-[70px]">
      <div className={`p-3 rounded-lg border flex items-center justify-center mb-2 bg-[#0d1117] ${colorClass}`}>
        <Icon className="h-5 w-5" />
      </div>
      <span className="text-[10px] font-medium text-foreground text-center leading-tight">{title}</span>
      {subtitle && <span className="text-[9px] text-muted-foreground text-center mt-0.5">{subtitle}</span>}
    </div>
  );

  const Arrow = () => (
    <div className="flex items-center justify-center text-muted-foreground px-1 sm:px-2 pb-6">
      <span className="text-sm">→</span>
    </div>
  );

  return (
    <div className="flex flex-col my-4 bg-[#161b22] border border-[#30363d] rounded-xl p-4 w-full">
      <div className="flex items-center justify-between mb-6">
        <span className="text-xs font-semibold text-foreground/90">RAG Pipeline Visualization</span>
        <button className="flex items-center text-[10px] text-muted-foreground hover:text-foreground transition-colors">
          View Full Pipeline <ExternalLink className="ml-1 h-3 w-3" />
        </button>
      </div>

      <div className="flex items-center justify-between w-full overflow-x-auto scrollbar-thin pb-2">
        <Node 
          icon={User} 
          title="User Query" 
          colorClass="border-green-500/30 text-green-500" 
        />
        <Arrow />
        <Node 
          icon={Search} 
          title="Retriever" 
          subtitle="(Hybrid Search)" 
          colorClass="border-blue-500/30 text-blue-500" 
        />
        <Arrow />
        <Node 
          icon={FileText} 
          title="Relevant Documents" 
          colorClass="border-yellow-500/30 text-yellow-500" 
        />
        <Arrow />
        <Node 
          icon={MessageSquare} 
          title="Augmented Prompt" 
          colorClass="border-purple-500/30 text-purple-500" 
        />
        <Arrow />
        <Node 
          icon={Sparkles} 
          title="LLM" 
          subtitle="(Generator)" 
          colorClass="border-orange-500/30 text-orange-500" 
        />
        <Arrow />
        <Node 
          icon={CheckCircle2} 
          title="Answer" 
          colorClass="border-teal-500/30 text-teal-500" 
        />
      </div>
    </div>
  );
}
