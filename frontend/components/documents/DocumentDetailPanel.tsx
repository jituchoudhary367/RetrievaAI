"use client";

import React, { useState } from 'react';
import { X, FileText, Copy, Eye, Download, Trash2, Plus } from 'lucide-react';

export function DocumentDetailPanel({ document, onClose }: any) {
  const [activeTab, setActiveTab] = useState('Overview');
  const tabs = ['Overview', 'Chunks', 'Metadata', 'Activity'];

  const getBigIcon = (type: string) => {
    switch (type) {
      case 'pdf': return <div className="w-12 h-12 rounded bg-red-500/10 text-red-500 border border-red-500/20 flex items-center justify-center flex-shrink-0 text-sm font-bold">PDF</div>;
      case 'md': return <div className="w-12 h-12 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20 flex items-center justify-center flex-shrink-0 text-sm font-bold">MD</div>;
      default: return <div className="w-12 h-12 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20 flex items-center justify-center flex-shrink-0"><FileText className="h-6 w-6" /></div>;
    }
  };

  if (!document) return null;

  return (
    <div className="flex flex-col h-full relative">
      
      {/* Header */}
      <div className="flex items-center justify-between p-6 pb-2">
        <h2 className="text-sm font-semibold text-foreground truncate pr-4">{document.title}</h2>
        <button onClick={onClose} className="text-muted-foreground hover:text-foreground transition-colors flex-shrink-0">
          <X className="h-5 w-5" />
        </button>
      </div>

      {/* Tabs */}
      <div className="flex items-center space-x-6 px-6 border-b border-[#30363d]">
        {tabs.map((tab) => (
          <button 
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`pb-3 text-xs font-medium transition-colors border-b-2 ${
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
        <div className="flex items-start space-x-4">
          {getBigIcon(document.type)}
          <div className="flex flex-col space-y-1 overflow-hidden">
            <span className="text-sm font-semibold text-foreground truncate">{document.title}</span>
            <span className="text-xs text-muted-foreground">{document.type.toUpperCase()} Document • {document.size}</span>
            <span className="text-[10px] font-mono text-muted-foreground mt-1 truncate">{document.source}</span>
            <span className="text-[10px] text-muted-foreground mt-1">Uploaded: {document.uploaded}</span>
            <span className="text-[10px] text-muted-foreground">Uploaded by: {document.uploader || 'System'}</span>
          </div>
        </div>

        {/* Quality Score */}
        {document.quality !== null && (
          <div className="flex items-center border border-[#10b981]/30 rounded-lg p-3 bg-[#122822]/50">
            <div className="flex flex-col items-center justify-center w-12 h-10 border-r border-[#10b981]/20 pr-3 mr-3">
              <span className="text-[#10b981] font-bold text-lg">{document.quality.toFixed(2)}</span>
            </div>
            <div className="flex flex-col">
              <span className="text-[10px] text-muted-foreground font-medium">Quality Score</span>
              <span className="text-[10px] text-[#10b981] font-medium">+ Excellent</span>
            </div>
          </div>
        )}

        {/* Quick Stats Grid */}
        <div className="grid grid-cols-4 gap-2">
          {[
            { label: 'Chunks', val: document.chunks },
            { label: 'Pages', val: document.pages || '-' },
            { label: 'Words', val: document.words || '-' },
            { label: 'Tokens', val: document.tokens || '-' },
          ].map((stat) => (
            <div key={stat.label} className="flex flex-col items-center justify-center bg-[#12181f] border border-[#1e2329] rounded-lg p-2 py-3">
              <span className="text-[10px] text-muted-foreground mb-1">{stat.label}</span>
              <span className="text-xs font-semibold text-foreground">{stat.val}</span>
            </div>
          ))}
        </div>

        {/* Tags */}
        <div className="flex flex-col space-y-3">
          <span className="text-xs font-semibold text-foreground">Tags</span>
          <div className="flex flex-wrap gap-2">
            {document.tags.map((tag: string) => (
              <span key={tag} className="text-[10px] px-2 py-1 bg-[#1e2329] border border-[#30363d] rounded-full text-muted-foreground">
                {tag}
              </span>
            ))}
            <button className="flex items-center justify-center w-6 h-6 rounded-full bg-[#1e2329] border border-[#30363d] text-muted-foreground hover:text-foreground transition-colors">
              <Plus className="h-3 w-3" />
            </button>
          </div>
        </div>

        {/* Description */}
        <div className="flex flex-col space-y-2">
          <span className="text-xs font-semibold text-foreground">Description</span>
          <p className="text-xs text-muted-foreground leading-relaxed">
            {document.description || "No description provided for this document."}
          </p>
          {document.description && (
            <button className="text-left text-[10px] text-blue-400 hover:text-blue-300 transition-colors">
              Show more
            </button>
          )}
        </div>

        {/* Source Info Table */}
        <div className="flex flex-col space-y-3">
          <span className="text-xs font-semibold text-foreground">Source Information</span>
          <div className="flex flex-col space-y-2">
            <div className="flex items-center justify-between border-b border-[#1e2329] pb-2">
              <span className="text-xs text-muted-foreground">Source Type</span>
              <span className="text-xs text-foreground uppercase">{document.type}</span>
            </div>
            <div className="flex items-center justify-between border-b border-[#1e2329] pb-2">
              <span className="text-xs text-muted-foreground">Original Filename</span>
              <span className="text-xs text-foreground truncate max-w-[180px] text-right" title={document.title}>{document.title.replace(/ /g, '_')}</span>
            </div>
            <div className="flex items-center justify-between border-b border-[#1e2329] pb-2">
              <span className="text-xs text-muted-foreground">File Path</span>
              <span className="text-[10px] text-foreground font-mono truncate max-w-[180px] text-right" title={`${document.source}/${document.title.replace(/ /g, '_')}`}>
                {document.source}/{document.title.replace(/ /g, '_')}
              </span>
            </div>
            <div className="flex items-center justify-between border-b border-[#1e2329] pb-2 group">
              <span className="text-xs text-muted-foreground">Checksum</span>
              <div className="flex items-center space-x-2">
                <span className="text-[10px] text-foreground font-mono">{document.checksum || 'N/A'}</span>
                <button className="text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity hover:text-foreground">
                  <Copy className="h-3 w-3" />
                </button>
              </div>
            </div>
          </div>
        </div>

      </div>

      {/* Footer Buttons Fixed */}
      <div className="absolute bottom-0 left-0 right-0 p-4 bg-[#0d1117] border-t border-[#30363d] flex items-center justify-between space-x-2">
        <button className="flex-1 flex items-center justify-center space-x-1 py-2 rounded border border-[#10b981]/50 text-[#10b981] hover:bg-[#10b981]/10 transition-colors text-xs font-medium">
          <Eye className="h-3.5 w-3.5" />
          <span>Preview</span>
        </button>
        <button className="flex-1 flex items-center justify-center space-x-1 py-2 rounded border border-[#30363d] text-muted-foreground hover:text-foreground hover:bg-[#30363d]/50 transition-colors text-xs font-medium">
          <Download className="h-3.5 w-3.5" />
          <span>Download</span>
        </button>
        <button className="flex-1 flex items-center justify-center space-x-1 py-2 rounded border border-red-500/50 text-red-500 hover:bg-red-500/10 transition-colors text-xs font-medium">
          <Trash2 className="h-3.5 w-3.5" />
          <span>Delete</span>
        </button>
      </div>

    </div>
  );
}
