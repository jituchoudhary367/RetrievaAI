"use client";

import React, { useState } from 'react';
import { Search, Filter, Eye, MoreVertical, FileText, CheckCircle2, Clock, XCircle, Loader2 } from 'lucide-react';

export function IngestionListArea({ jobs, selectedJobId, onSelectJob }: any) {
  const [activeTab, setActiveTab] = useState('All Ingestions');
  const tabs = ['All Ingestions', 'Processing', 'Completed', 'Failed', 'Scheduled'];

  const getIcon = (type: string) => {
    switch (type) {
      case 'pdf': return <div className="w-7 h-7 rounded bg-red-500/10 text-red-500 border border-red-500/20 flex items-center justify-center flex-shrink-0 text-[10px] font-bold">PDF</div>;
      case 'docx': return <div className="w-7 h-7 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20 flex items-center justify-center flex-shrink-0 text-[9px] font-bold">DOCX</div>;
      case 'md': return <div className="w-7 h-7 rounded bg-purple-500/10 text-purple-400 border border-purple-500/20 flex items-center justify-center flex-shrink-0 text-[10px] font-bold">MD</div>;
      case 'pptx': return <div className="w-7 h-7 rounded bg-orange-500/10 text-orange-500 border border-orange-500/20 flex items-center justify-center flex-shrink-0 text-[9px] font-bold">PPTX</div>;
      case 'csv': return <div className="w-7 h-7 rounded bg-green-500/10 text-green-500 border border-green-500/20 flex items-center justify-center flex-shrink-0 text-[10px] font-bold">CSV</div>;
      case 'zip': return <div className="w-7 h-7 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 flex items-center justify-center flex-shrink-0 text-[10px] font-bold">ZIP</div>;
      default: return <div className="w-7 h-7 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20 flex items-center justify-center flex-shrink-0"><FileText className="h-4 w-4" /></div>;
    }
  };

  const getStatusDisplay = (status: string) => {
    switch (status) {
      case 'Completed': return <div className="flex items-center space-x-1.5 text-[#10b981]"><CheckCircle2 className="w-3.5 h-3.5" /><span>Completed</span></div>;
      case 'Processing': return <div className="flex items-center space-x-1.5 text-[#3b82f6]"><Loader2 className="w-3.5 h-3.5 animate-spin" /><span>Processing</span></div>;
      case 'Queued': return <div className="flex items-center space-x-1.5 text-yellow-500"><Clock className="w-3.5 h-3.5" /><span>Queued</span></div>;
      case 'Failed': return <div className="flex items-center space-x-1.5 text-red-500"><XCircle className="w-3.5 h-3.5" /><span>Failed</span></div>;
      default: return <span>{status}</span>;
    }
  };

  const getProgressBar = (progress: number, status: string) => {
    let color = 'bg-[#10b981]';
    if (status === 'Processing') color = 'bg-[#3b82f6]';
    if (status === 'Failed') color = 'bg-red-500';

    return (
      <div className="flex items-center space-x-3 w-full">
        <div className="flex-1 h-1.5 bg-[#1e2329] rounded-full overflow-hidden">
          <div className={`h-full rounded-full ${color}`} style={{ width: `${progress}%` }} />
        </div>
        <span className="text-[10px] text-muted-foreground w-6">{progress}%</span>
      </div>
    );
  };

  return (
    <div className="w-full flex flex-col mt-6">
      
      {/* Tabs & Search Row */}
      <div className="flex flex-col md:flex-row items-end md:items-center justify-between border-b border-[#30363d] pb-4 mb-4 space-y-4 md:space-y-0">
        
        {/* Tabs */}
        <div className="flex items-center space-x-6">
          {tabs.map((tab) => (
            <button 
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`pb-4 -mb-[17px] text-xs font-semibold transition-colors border-b-2 ${
                activeTab === tab 
                  ? 'border-[#10b981] text-[#10b981]' 
                  : 'border-transparent text-muted-foreground hover:text-foreground hover:border-[#4b5563]'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>

        {/* Search & Filter */}
        <div className="flex items-center space-x-3">
          <div className="relative flex items-center w-64 bg-transparent border border-[#30363d] rounded-md px-3 py-1.5 focus-within:border-[#10b981] transition-colors">
            <Search className="h-3.5 w-3.5 text-muted-foreground mr-2" />
            <input 
              type="text" 
              className="flex-1 bg-transparent border-none outline-none text-foreground text-xs placeholder-muted-foreground"
              placeholder="Search by name or source..."
            />
          </div>
          <button className="flex items-center space-x-1 px-3 py-1.5 border border-[#30363d] rounded-md text-xs text-muted-foreground hover:text-foreground transition-colors">
            <Filter className="h-3.5 w-3.5" />
            <span>Filter</span>
            <span className="text-[10px] ml-1">⌄</span>
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="w-full overflow-x-auto">
        <table className="w-full text-left text-xs text-muted-foreground border-collapse">
          <thead>
            <tr className="border-b border-[#1e2329] text-[10px] uppercase tracking-wider text-muted-foreground/70">
              <th className="px-4 py-3 font-medium">Name</th>
              <th className="px-4 py-3 font-medium">Source</th>
              <th className="px-4 py-3 font-medium min-w-[120px]">Status</th>
              <th className="px-4 py-3 font-medium min-w-[140px]">Progress</th>
              <th className="px-4 py-3 font-medium">Chunks</th>
              <th className="px-4 py-3 font-medium">Indexed</th>
              <th className="px-4 py-3 font-medium">Started</th>
              <th className="px-4 py-3 font-medium text-center">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#1e2329]">
            {jobs.map((job: any) => (
              <tr 
                key={job.id} 
                onClick={() => onSelectJob(job.id)}
                className={`group transition-colors cursor-pointer ${
                  selectedJobId === job.id ? 'bg-[#161b22]' : 'hover:bg-[#12181f]'
                }`}
              >
                <td className="px-4 py-3 min-w-[280px]">
                  <div className="flex items-start space-x-3">
                    <div className="mt-0.5">{getIcon(job.type)}</div>
                    <div className="flex flex-col space-y-0.5">
                      <span className="text-xs font-semibold text-foreground group-hover:text-primary transition-colors">
                        {job.title}
                      </span>
                      <span className="text-[10px] text-muted-foreground">
                        {job.subtitle}
                      </span>
                    </div>
                  </div>
                </td>
                
                <td className="px-4 py-3 font-mono text-[9px] whitespace-nowrap text-muted-foreground/80">{job.source}</td>
                <td className="px-4 py-3 whitespace-nowrap">{getStatusDisplay(job.status)}</td>
                <td className="px-4 py-3">{getProgressBar(job.progress, job.status)}</td>
                <td className="px-4 py-3 whitespace-nowrap">{job.chunks}</td>
                <td className="px-4 py-3 whitespace-nowrap">{job.indexed}</td>
                <td className="px-4 py-3 whitespace-nowrap text-[10px]">{job.started}</td>
                <td className="px-4 py-3">
                  <div className="flex items-center justify-center space-x-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button className="p-1 text-muted-foreground hover:text-foreground transition-colors" title="View details">
                      <Eye className="h-3.5 w-3.5" />
                    </button>
                    <button className="p-1 text-muted-foreground hover:text-foreground transition-colors">
                      <MoreVertical className="h-3.5 w-3.5" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      <div className="flex items-center justify-between mt-6 px-4">
        <div className="flex items-center space-x-1 border border-[#30363d] rounded p-0.5">
          <button className="w-6 h-6 rounded flex items-center justify-center text-muted-foreground hover:bg-[#30363d] transition-colors text-[10px] font-medium">&lt;</button>
          <button className="w-6 h-6 rounded flex items-center justify-center bg-[#10b981] text-background text-[10px] font-medium">1</button>
          <button className="w-6 h-6 rounded flex items-center justify-center text-muted-foreground hover:bg-[#30363d] transition-colors text-[10px] font-medium">2</button>
          <button className="w-6 h-6 rounded flex items-center justify-center text-muted-foreground hover:bg-[#30363d] transition-colors text-[10px] font-medium">3</button>
          <button className="w-6 h-6 rounded flex items-center justify-center text-muted-foreground hover:bg-[#30363d] transition-colors text-[10px] font-medium">4</button>
          <button className="w-6 h-6 rounded flex items-center justify-center text-muted-foreground hover:bg-[#30363d] transition-colors text-[10px] font-medium">5</button>
          <span className="px-1 text-muted-foreground text-[10px]">...</span>
          <button className="w-6 h-6 rounded flex items-center justify-center text-muted-foreground hover:bg-[#30363d] transition-colors text-[10px] font-medium">25</button>
          <button className="w-6 h-6 rounded flex items-center justify-center text-muted-foreground hover:bg-[#30363d] transition-colors text-[10px] font-medium">&gt;</button>
        </div>
        <span className="text-[10px] text-muted-foreground">Showing 1 to 6 of 148 ingestions</span>
      </div>

    </div>
  );
}
