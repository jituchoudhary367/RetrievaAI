"use client";

import React, { useState } from 'react';
import { X, FileText, Download, Trash2, Box } from 'lucide-react';

export function IngestionDetailPanel({ job, onClose }: any) {
  const [activeTab, setActiveTab] = useState('Overview');
  const tabs = ['Overview', 'Chunks', 'Metadata', 'Logs'];

  const getBigIcon = (type: string) => {
    switch (type) {
      case 'pdf': return <div className="w-10 h-10 rounded bg-red-500/10 text-red-500 border border-red-500/20 flex items-center justify-center flex-shrink-0 text-[10px] font-bold">PDF</div>;
      case 'docx': return <div className="w-10 h-10 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20 flex items-center justify-center flex-shrink-0 text-[10px] font-bold">DOCX</div>;
      case 'md': return <div className="w-10 h-10 rounded bg-purple-500/10 text-purple-400 border border-purple-500/20 flex items-center justify-center flex-shrink-0 text-[10px] font-bold">MD</div>;
      default: return <div className="w-10 h-10 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20 flex items-center justify-center flex-shrink-0"><FileText className="h-5 w-5" /></div>;
    }
  };

  if (!job) return null;

  return (
    <div className="flex flex-col h-full relative">
      
      {/* Header */}
      <div className="flex items-center justify-between p-6 pb-2">
        <h2 className="text-xs font-semibold text-foreground truncate pr-4">{job.title}</h2>
        <button onClick={onClose} className="text-muted-foreground hover:text-foreground transition-colors flex-shrink-0">
          <X className="h-4 w-4" />
        </button>
      </div>

      {/* Tabs */}
      <div className="flex items-center space-x-6 px-6 border-b border-[#30363d]">
        {tabs.map((tab) => (
          <button 
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`pb-3 text-[10px] font-medium transition-colors border-b-2 ${
              activeTab === tab 
                ? 'border-[#10b981] text-[#10b981]' 
                : 'border-transparent text-muted-foreground hover:text-foreground hover:border-[#4b5563]'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-8 pb-24 scrollbar-thin">
        
        {/* Hero Card */}
        <div className="flex items-start space-x-3">
          {getBigIcon(job.type)}
          <div className="flex flex-col space-y-1 overflow-hidden mt-0.5">
            <span className="text-xs font-semibold text-foreground truncate">{job.title}</span>
            <span className="text-[9px] font-mono text-muted-foreground truncate">{job.source}</span>
            <span className="text-[9px] text-muted-foreground">Uploaded: {job.started}</span>
            <span className="text-[9px] text-muted-foreground">Uploaded by: {job.uploader || 'Admin User'}</span>
          </div>
        </div>

        {/* Details List */}
        <div className="flex flex-col space-y-3">
          <div className="flex items-center justify-between border-b border-[#1e2329] pb-2">
            <span className="text-[10px] text-muted-foreground">Status</span>
            <span className="text-[10px] font-medium text-[#10b981]">{job.status}</span>
          </div>
          <div className="flex items-center justify-between border-b border-[#1e2329] pb-2">
            <span className="text-[10px] text-muted-foreground">File Size</span>
            <span className="text-[10px] text-foreground">{job.subtitle.split('•')[0].trim()}</span>
          </div>
          <div className="flex items-center justify-between border-b border-[#1e2329] pb-2">
            <span className="text-[10px] text-muted-foreground">Pages</span>
            <span className="text-[10px] text-foreground">{job.subtitle.split('•')[1]?.trim().split(' ')[0] || '-'}</span>
          </div>
          <div className="flex items-center justify-between border-b border-[#1e2329] pb-2">
            <span className="text-[10px] text-muted-foreground">Chunks</span>
            <span className="text-[10px] text-foreground">{job.chunks}</span>
          </div>
          <div className="flex items-center justify-between border-b border-[#1e2329] pb-2">
            <span className="text-[10px] text-muted-foreground">Indexed</span>
            <span className="text-[10px] text-foreground">{job.indexed} / {job.chunks}</span>
          </div>
          <div className="flex items-center justify-between border-b border-[#1e2329] pb-2">
            <span className="text-[10px] text-muted-foreground">Processing Time</span>
            <span className="text-[10px] text-foreground">{job.processingTime || 'N/A'}</span>
          </div>
          <div className="flex items-center justify-between border-b border-[#1e2329] pb-2">
            <span className="text-[10px] text-muted-foreground">Embedding Model</span>
            <span className="text-[10px] text-foreground">{job.model || 'N/A'}</span>
          </div>
          <div className="flex items-center justify-between border-b border-[#1e2329] pb-2">
            <span className="text-[10px] text-muted-foreground">Parser</span>
            <span className="text-[10px] text-foreground">{job.parser || 'N/A'}</span>
          </div>
          <div className="flex items-center justify-between border-b border-[#1e2329] pb-2">
            <span className="text-[10px] text-muted-foreground">Chunk Size</span>
            <span className="text-[10px] text-foreground">{job.chunkSize || 'N/A'}</span>
          </div>
          <div className="flex items-center justify-between pb-2">
            <span className="text-[10px] text-muted-foreground">Chunk Overlap</span>
            <span className="text-[10px] text-foreground">{job.chunkOverlap || 'N/A'}</span>
          </div>
        </div>

        {/* Preview */}
        <div className="flex flex-col space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-foreground">Preview</span>
            <span className="text-[9px] text-muted-foreground">Page 1 of {job.subtitle.split('•')[1]?.trim().split(' ')[0] || '1'}</span>
          </div>
          <div className="w-full h-32 bg-[#12181f] border border-[#1e2329] rounded-lg flex items-center justify-center p-2">
            {/* SVG Flowchart Mock */}
            <svg viewBox="0 0 200 100" className="w-full h-full opacity-60">
              <rect x="20" y="40" width="30" height="20" rx="4" fill="none" stroke="#30363d" strokeWidth="1" />
              <rect x="85" y="20" width="30" height="60" rx="4" fill="none" stroke="#30363d" strokeWidth="1" />
              <rect x="150" y="40" width="30" height="20" rx="4" fill="none" stroke="#30363d" strokeWidth="1" />
              
              <path d="M 50 50 L 85 50" fill="none" stroke="#10b981" strokeWidth="1" markerEnd="url(#arrow)" />
              <path d="M 115 50 L 150 50" fill="none" stroke="#10b981" strokeWidth="1" markerEnd="url(#arrow)" />
              
              <text x="35" y="52" fontSize="5" fill="#8b949e" textAnchor="middle">Input</text>
              <text x="100" y="52" fontSize="5" fill="#8b949e" textAnchor="middle">Process</text>
              <text x="165" y="52" fontSize="5" fill="#8b949e" textAnchor="middle">Output</text>
            </svg>
          </div>
        </div>

      </div>

      {/* Footer Buttons Fixed */}
      <div className="absolute bottom-0 left-0 right-0 p-4 bg-[#0d1117] border-t border-[#30363d] flex items-center justify-between space-x-2">
        <button className="flex-1 flex items-center justify-center space-x-1 py-1.5 rounded border border-[#30363d] text-muted-foreground hover:text-foreground hover:bg-[#30363d]/50 transition-colors text-[10px] font-medium">
          <Box className="h-3 w-3" />
          <span>View Chunks</span>
        </button>
        <button className="flex-1 flex items-center justify-center space-x-1 py-1.5 rounded border border-[#30363d] text-muted-foreground hover:text-foreground hover:bg-[#30363d]/50 transition-colors text-[10px] font-medium">
          <Download className="h-3 w-3" />
          <span>Download</span>
        </button>
        <button className="flex-1 flex items-center justify-center space-x-1 py-1.5 rounded border border-red-500/50 text-red-500 hover:bg-red-500/10 transition-colors text-[10px] font-medium">
          <Trash2 className="h-3 w-3" />
          <span>Delete</span>
        </button>
      </div>

    </div>
  );
}
