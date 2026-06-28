"use client";

import React from 'react';
import { CheckCircle2, ChevronRight, FileText } from 'lucide-react';

export function AnalyticsRightPanel() {
  
  const getIcon = (type: string) => {
    if (type === 'pdf') return <div className="w-5 h-5 rounded bg-red-500/10 text-red-500 flex items-center justify-center flex-shrink-0 text-[7px] font-bold">PDF</div>;
    return <div className="w-5 h-5 rounded bg-blue-500/10 text-blue-400 flex items-center justify-center flex-shrink-0 text-[7px] font-bold">MD</div>;
  };

  return (
    <div className="flex-1 flex flex-col p-6 space-y-6">
      
      {/* System Health */}
      <div className="flex flex-col space-y-4 pb-6 border-b border-[#30363d]">
        <span className="text-xs font-semibold text-foreground">System Health</span>
        <div className="flex items-center space-x-2 text-[10px] text-muted-foreground -mt-2">
          <span>All systems operational</span>
          <CheckCircle2 className="w-3.5 h-3.5 text-[#10b981]" />
        </div>
        
        <div className="flex flex-col space-y-2.5">
          {[
            { name: 'Qdrant', uptime: '99.9%' },
            { name: 'Redis', uptime: '100%' },
            { name: 'LLM API (Groq)', uptime: '99.8%' },
            { name: 'Embedding API', uptime: '99.7%' },
          ].map(sys => (
            <div key={sys.name} className="flex items-center justify-between text-[10px]">
              <div className="flex items-center space-x-2">
                <div className="w-1.5 h-1.5 rounded-full bg-[#10b981]" />
                <span className="text-muted-foreground">{sys.name}</span>
              </div>
              <div className="flex items-center space-x-3">
                <span className="text-[#10b981]">Healthy</span>
                <span className="text-foreground w-8 text-right">{sys.uptime}</span>
              </div>
            </div>
          ))}
        </div>
        
        <div className="text-center mt-2">
          <span className="text-[10px] text-[#10b981] hover:text-[#059669] transition-colors cursor-pointer inline-flex items-center">
            View all systems <span className="ml-1">→</span>
          </span>
        </div>
      </div>

      {/* Top Queries */}
      <div className="flex flex-col space-y-4 pb-6 border-b border-[#30363d]">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-foreground">Top Queries</span>
          <span className="text-[10px] text-muted-foreground hover:text-foreground cursor-pointer">View all</span>
        </div>
        
        <div className="flex flex-col space-y-3 text-[10px]">
          {[
            { q: 'What is RAG and how does it work?', v: 423, bg: 'bg-[#10b981]/20 text-[#10b981]' },
            { q: 'Explain CRAG pipeline', v: 312, bg: 'bg-[#3b82f6]/20 text-[#3b82f6]' },
            { q: 'Hybrid search vs BM25', v: 288, bg: 'bg-[#8b5cf6]/20 text-[#8b5cf6]' },
            { q: 'How reranking improves results?', v: 256, bg: 'bg-yellow-500/20 text-yellow-500' },
            { q: 'Best chunking strategies?', v: 214, bg: 'bg-yellow-600/20 text-yellow-600' },
          ].map((item, i) => (
            <div key={i} className="flex items-center justify-between group cursor-pointer">
              <div className="flex items-center space-x-2 overflow-hidden pr-2">
                <div className={`w-3.5 h-3.5 rounded flex items-center justify-center flex-shrink-0 text-[8px] font-bold ${item.bg}`}>
                  {i + 1}
                </div>
                <span className="text-muted-foreground group-hover:text-foreground transition-colors truncate">{item.q}</span>
              </div>
              <div className="flex items-center space-x-1 flex-shrink-0 text-muted-foreground group-hover:text-foreground transition-colors">
                <span>{item.v}</span>
                <ChevronRight className="w-3 h-3" />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Top Sources */}
      <div className="flex flex-col space-y-4 pb-6 border-b border-[#30363d]">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-foreground">Top Sources</span>
          <span className="text-[10px] text-muted-foreground hover:text-foreground cursor-pointer">View all</span>
        </div>
        
        <div className="flex flex-col space-y-3">
          {[
            { t: 'pdf', n: 'rag_overview.pdf', v: '1,248', p: 24, c: 'bg-[#10b981]' },
            { t: 'md', n: 'huggingface_rag_blog.md', v: '987', p: 19, c: 'bg-[#3b82f6]' },
            { t: 'pdf', n: 'langchain_documentation.pdf', v: '856', p: 16, c: 'bg-red-500' },
            { t: 'pdf', n: 'production_rag_guide.pdf', v: '742', p: 14, c: 'bg-red-400' },
            { t: 'md', n: 'vector_search_tutorial.md', v: '621', p: 12, c: 'bg-[#3b82f6]' },
          ].map((src, i) => (
            <div key={i} className="flex flex-col space-y-1.5 cursor-pointer group">
              <div className="flex items-center justify-between text-[10px]">
                <div className="flex items-center space-x-2 overflow-hidden pr-2">
                  {getIcon(src.t)}
                  <span className="text-muted-foreground group-hover:text-foreground transition-colors truncate">{src.n}</span>
                </div>
                <div className="flex items-center space-x-2 flex-shrink-0">
                  <span className="text-foreground font-medium">{src.v}</span>
                  <span className="text-muted-foreground w-6 text-right">{src.p}%</span>
                </div>
              </div>
              <div className="w-full h-1 bg-[#1e2329] rounded-full overflow-hidden">
                <div className={`h-full rounded-full ${src.c}`} style={{ width: `${src.p}%` }} />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Cost Breakdown */}
      <div className="flex flex-col space-y-4 pb-6">
        <span className="text-xs font-semibold text-foreground">Cost Breakdown (USD)</span>
        
        <div className="flex items-center space-x-4">
          <div className="relative w-24 h-24 flex-shrink-0">
            {/* Cost SVG Donut */}
            <svg viewBox="0 0 100 100" className="w-full h-full transform -rotate-90">
              <circle cx="50" cy="50" r="40" fill="transparent" stroke="#1e2329" strokeWidth="16" />
              {/* LLM (Blue) 56% */}
              <circle cx="50" cy="50" r="40" fill="transparent" stroke="#3b82f6" strokeWidth="16" strokeDasharray={`${56 * 2.51} 251`} strokeDashoffset="0" />
              {/* Embed (Green) 24% */}
              <circle cx="50" cy="50" r="40" fill="transparent" stroke="#10b981" strokeWidth="16" strokeDasharray={`${24 * 2.51} 251`} strokeDashoffset={`-${56 * 2.51}`} />
              {/* Rerank (Purple) 13% */}
              <circle cx="50" cy="50" r="40" fill="transparent" stroke="#8b5cf6" strokeWidth="16" strokeDasharray={`${13 * 2.51} 251`} strokeDashoffset={`-${80 * 2.51}`} />
              {/* Other (Orange) 7% */}
              <circle cx="50" cy="50" r="40" fill="transparent" stroke="#f97316" strokeWidth="16" strokeDasharray={`${7 * 2.51} 251`} strokeDashoffset={`-${93 * 2.51}`} />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
              <span className="text-[10px] font-bold text-foreground">$48.67</span>
              <span className="text-[8px] text-muted-foreground">Total</span>
            </div>
          </div>
          
          <div className="flex-1 flex flex-col space-y-2 text-[9px]">
            {[
              { label: 'LLM (Completions)', val: '$27.34', pct: '56%', color: 'bg-[#3b82f6]' },
              { label: 'Embeddings', val: '$11.82', pct: '24%', color: 'bg-[#10b981]' },
              { label: 'Reranking', val: '$6.21', pct: '13%', color: 'bg-[#8b5cf6]' },
              { label: 'Other Services', val: '$3.30', pct: '7%', color: 'bg-[#f97316]' },
            ].map(c => (
              <div key={c.label} className="flex items-center justify-between">
                <div className="flex items-center space-x-1.5">
                  <div className={`w-1.5 h-1.5 rounded-full ${c.color}`} />
                  <span className="text-muted-foreground">{c.label}</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-foreground">{c.val}</span>
                  <span className="text-muted-foreground w-4 text-right">{c.pct}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="text-center mt-2">
          <span className="text-[10px] text-[#10b981] hover:text-[#059669] transition-colors cursor-pointer inline-flex items-center">
            View detailed billing <span className="ml-1">→</span>
          </span>
        </div>
      </div>

    </div>
  );
}
