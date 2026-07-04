"use client";

import React, { useState } from 'react';
import { Search, Filter, Eye, MoreVertical, FileText, CheckCircle2, Clock, XCircle, Loader2 } from 'lucide-react';

export function IngestionListArea({ jobs, selectedJobId, onSelectJob }: any) {
  const [activeTab, setActiveTab] = useState('All Ingestions');
  const [searchQuery, setSearchQuery] = useState('');
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

  // Backend returns lowercase statuses: completed, processing, queued, failed
  const getStatusDisplay = (status: string) => {
    const s = (status || '').toLowerCase();
    switch (s) {
      case 'completed': return <div className="flex items-center space-x-1.5 text-[#10b981]"><CheckCircle2 className="w-3.5 h-3.5" /><span>Completed</span></div>;
      case 'processing': return <div className="flex items-center space-x-1.5 text-[#3b82f6]"><Loader2 className="w-3.5 h-3.5 animate-spin" /><span>Processing</span></div>;
      case 'queued': return <div className="flex items-center space-x-1.5 text-yellow-500"><Clock className="w-3.5 h-3.5" /><span>Queued</span></div>;
      case 'failed': return <div className="flex items-center space-x-1.5 text-red-500"><XCircle className="w-3.5 h-3.5" /><span>Failed</span></div>;
      case 'cancelled': return <div className="flex items-center space-x-1.5 text-zinc-400"><XCircle className="w-3.5 h-3.5" /><span>Cancelled</span></div>;
      default: return <span className="capitalize">{status}</span>;
    }
  };

  const getProgressBar = (progress: number, status: string) => {
    const s = (status || '').toLowerCase();
    let color = 'bg-[#10b981]';
    if (s === 'processing') color = 'bg-[#3b82f6]';
    if (s === 'failed') color = 'bg-red-500';

    return (
      <div className="flex items-center space-x-3 w-full">
        <div className="flex-1 h-1.5 bg-[#1e2329] rounded-full overflow-hidden">
          <div className={`h-full rounded-full ${color}`} style={{ width: `${progress ?? 0}%` }} />
        </div>
        <span className="text-[10px] text-muted-foreground w-6">{progress ?? 0}%</span>
      </div>
    );
  };

  // Filter jobs based on active tab (real-time filtering)
  const filteredJobs = (jobs || []).filter((job: any) => {
    const statusLower = (job.status || '').toLowerCase();
    const tabMatch = (() => {
      switch (activeTab) {
        case 'All Ingestions': return true;
        case 'Processing': return statusLower === 'processing' || statusLower === 'queued';
        case 'Completed': return statusLower === 'completed';
        case 'Failed': return statusLower === 'failed' || statusLower === 'cancelled';
        case 'Scheduled': return statusLower === 'scheduled';
        default: return true;
      }
    })();

    const searchMatch = !searchQuery || 
      (job.title || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
      (job.source || '').toLowerCase().includes(searchQuery.toLowerCase());

    return tabMatch && searchMatch;
  });

  // Count per tab for badges
  const counts: Record<string, number> = {
    'All Ingestions': (jobs || []).length,
    'Processing': (jobs || []).filter((j: any) => ['processing', 'queued'].includes((j.status || '').toLowerCase())).length,
    'Completed': (jobs || []).filter((j: any) => (j.status || '').toLowerCase() === 'completed').length,
    'Failed': (jobs || []).filter((j: any) => ['failed', 'cancelled'].includes((j.status || '').toLowerCase())).length,
    'Scheduled': (jobs || []).filter((j: any) => (j.status || '').toLowerCase() === 'scheduled').length,
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
              className={`pb-4 -mb-[17px] text-xs font-semibold transition-colors border-b-2 flex items-center gap-1.5 ${
                activeTab === tab 
                  ? 'border-[#10b981] text-[#10b981]' 
                  : 'border-transparent text-muted-foreground hover:text-foreground hover:border-[#4b5563]'
              }`}
            >
              {tab}
              {counts[tab] > 0 && (
                <span className={`text-[9px] px-1.5 py-0.5 rounded-full font-bold ${
                  activeTab === tab ? 'bg-[#10b981]/20 text-[#10b981]' : 'bg-[#1e2329] text-muted-foreground'
                }`}>
                  {counts[tab]}
                </span>
              )}
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
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
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
            {filteredJobs.length === 0 ? (
              <tr>
                <td colSpan={8} className="px-4 py-10 text-center text-muted-foreground text-xs">
                  {searchQuery ? `No jobs match "${searchQuery}"` : `No ${activeTab === 'All Ingestions' ? '' : activeTab.toLowerCase() + ' '}jobs found`}
                </td>
              </tr>
            ) : (
              filteredJobs.map((job: any) => (
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
                  <td className="px-4 py-3 whitespace-nowrap">{job.chunks ?? 0}</td>
                  <td className="px-4 py-3 whitespace-nowrap">{job.indexed ?? 0}</td>
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
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
