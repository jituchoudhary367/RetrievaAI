"use client";

import React, { useState } from 'react';
import { Search, Filter, Tags, FileText, Code, Eye, Download, MoreVertical, LayoutGrid, List } from 'lucide-react';

export function DocumentListArea({ documents, selectedDocId, onSelectDoc }: any) {
  const [searchQuery, setSearchQuery] = useState("");

  const getIcon = (type: string) => {
    switch (type) {
      case 'pdf': return <div className="w-7 h-7 rounded bg-red-500/10 text-red-500 border border-red-500/20 flex items-center justify-center flex-shrink-0 text-[10px] font-bold">PDF</div>;
      case 'md': return <div className="w-7 h-7 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20 flex items-center justify-center flex-shrink-0 text-[10px] font-bold">MD</div>;
      case 'ppt': return <div className="w-7 h-7 rounded bg-orange-500/10 text-orange-500 border border-orange-500/20 flex items-center justify-center flex-shrink-0 text-[10px] font-bold">PPT</div>;
      case 'txt': return <div className="w-7 h-7 rounded bg-gray-500/10 text-gray-400 border border-gray-500/20 flex items-center justify-center flex-shrink-0 text-[10px] font-bold">TXT</div>;
      case 'code': return <div className="w-7 h-7 rounded bg-purple-500/10 text-purple-400 border border-purple-500/20 flex items-center justify-center flex-shrink-0 text-[8px] font-bold">CODE</div>;
      default: return <div className="w-7 h-7 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20 flex items-center justify-center flex-shrink-0"><FileText className="h-4 w-4" /></div>;
    }
  };

  const getScoreColor = (score: number | null) => {
    if (score === null) return 'text-muted-foreground';
    if (score >= 0.8) return 'text-[#10b981]';
    if (score >= 0.5) return 'text-yellow-500';
    return 'text-red-500';
  };

  return (
    <div className="w-full flex flex-col mt-4">
      
      {/* Filter Row */}
      <div className="flex flex-col md:flex-row items-center justify-between mb-4 space-y-4 md:space-y-0">
        <div className="flex items-center space-x-3 w-full md:w-auto">
          {/* Search Box */}
          <div className="relative flex items-center w-64 bg-transparent border border-[#30363d] rounded-md px-3 py-1.5 focus-within:border-[#10b981] transition-colors">
            <Search className="h-4 w-4 text-muted-foreground mr-2" />
            <input 
              type="text" 
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="flex-1 bg-transparent border-none outline-none text-foreground text-xs placeholder-muted-foreground"
              placeholder="Search documents by name, source, tag..."
            />
          </div>

          {/* Filter Chips */}
          <button className="flex items-center space-x-1 px-3 py-1.5 border border-[#30363d] rounded-md text-xs text-muted-foreground hover:text-foreground transition-colors">
            <Filter className="h-3.5 w-3.5" />
            <span>Filter</span>
            <span className="text-[10px] ml-1">⌄</span>
          </button>
          
          <button className="flex items-center space-x-1 px-3 py-1.5 border border-[#30363d] rounded-md text-xs text-muted-foreground hover:text-foreground transition-colors">
            <Tags className="h-3.5 w-3.5" />
            <span>Tags</span>
            <span className="text-[10px] ml-1">⌄</span>
          </button>
          
          <button className="flex items-center space-x-1 px-3 py-1.5 border border-[#30363d] rounded-md text-xs text-muted-foreground hover:text-foreground transition-colors">
            <FileText className="h-3.5 w-3.5" />
            <span>Source</span>
            <span className="text-[10px] ml-1">⌄</span>
          </button>
        </div>

        {/* Right side controls */}
        <div className="flex items-center space-x-4 w-full md:w-auto justify-end">
          <div className="flex items-center text-xs text-muted-foreground space-x-1 cursor-pointer hover:text-foreground">
            <span>Sort:</span>
            <span className="font-medium text-foreground">Newest First</span>
            <span className="ml-1 text-[10px]">⌄</span>
          </div>
          <div className="flex items-center border border-[#30363d] rounded-md overflow-hidden">
            <button className="p-1.5 bg-[#122822] text-[#10b981] hover:bg-[#1a382f] transition-colors">
              <List className="h-4 w-4" />
            </button>
            <button className="p-1.5 bg-transparent text-muted-foreground hover:text-foreground hover:bg-[#30363d]/50 transition-colors">
              <LayoutGrid className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="w-full overflow-x-auto rounded-lg border border-[#1e2329] bg-[#0d1117]/50">
        <table className="w-full text-left text-xs text-muted-foreground border-collapse">
          <thead>
            <tr className="border-b border-[#1e2329] text-[11px] uppercase tracking-wider text-muted-foreground/70">
              <th className="px-4 py-3 font-medium">Document</th>
              <th className="px-4 py-3 font-medium">Source</th>
              <th className="px-4 py-3 font-medium">Chunks</th>
              <th className="px-4 py-3 font-medium">Size</th>
              <th className="px-4 py-3 font-medium">Uploaded</th>
              <th className="px-4 py-3 font-medium">Quality</th>
              <th className="px-4 py-3 font-medium text-center">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#1e2329]">
            {documents.map((doc: any) => (
              <tr 
                key={doc.id} 
                onClick={() => onSelectDoc(doc.id)}
                className={`group transition-colors cursor-pointer ${
                  selectedDocId === doc.id ? 'bg-[#161b22] border-l-2 border-l-[#10b981]' : 'hover:bg-[#12181f] border-l-2 border-l-transparent'
                }`}
              >
                {/* Document Column */}
                <td className="px-4 py-3 min-w-[280px]">
                  <div className="flex items-start space-x-3">
                    <div className="mt-0.5">{getIcon(doc.type)}</div>
                    <div className="flex flex-col space-y-1">
                      <span className="text-sm font-semibold text-foreground group-hover:text-primary transition-colors">
                        {doc.title}
                      </span>
                      <div className="flex flex-wrap gap-1 mt-0.5">
                        {doc.tags.map((tag: string) => (
                          <span key={tag} className="text-[9px] px-1.5 py-0.5 bg-[#1e2329] rounded text-muted-foreground/90">
                            {tag}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </td>
                
                <td className="px-4 py-3 font-mono text-[10px] whitespace-nowrap">{doc.source}</td>
                <td className="px-4 py-3 whitespace-nowrap">{doc.chunks}</td>
                <td className="px-4 py-3 whitespace-nowrap">{doc.size}</td>
                <td className="px-4 py-3 whitespace-nowrap">
                  <div className="flex flex-col">
                    <span>{doc.uploaded.split(' ')[0] + ' ' + doc.uploaded.split(' ')[1] + ' ' + doc.uploaded.split(' ')[2]}</span>
                    <span className="text-[10px] text-muted-foreground/60">{doc.uploaded.split(' ')[3] + ' ' + doc.uploaded.split(' ')[4]}</span>
                  </div>
                </td>
                <td className="px-4 py-3 whitespace-nowrap font-medium">
                  <span className={getScoreColor(doc.quality)}>
                    {doc.quality !== null ? doc.quality.toFixed(2) : '-'}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center justify-center space-x-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button className="p-1 text-muted-foreground hover:text-foreground transition-colors" title="Preview">
                      <Eye className="h-4 w-4" />
                    </button>
                    <button className="p-1 text-muted-foreground hover:text-foreground transition-colors" title="Download">
                      <Download className="h-4 w-4" />
                    </button>
                    <button className="p-1 text-muted-foreground hover:text-foreground transition-colors">
                      <MoreVertical className="h-4 w-4" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      <div className="flex items-center justify-between mt-6 px-1">
        <div className="flex items-center space-x-1">
          <button className="w-6 h-6 rounded flex items-center justify-center text-muted-foreground hover:bg-[#30363d] transition-colors text-xs font-medium">&lt;</button>
          <button className="w-6 h-6 rounded flex items-center justify-center bg-[#10b981] text-background text-xs font-medium">1</button>
          <button className="w-6 h-6 rounded flex items-center justify-center text-muted-foreground hover:bg-[#30363d] transition-colors text-xs font-medium">2</button>
          <button className="w-6 h-6 rounded flex items-center justify-center text-muted-foreground hover:bg-[#30363d] transition-colors text-xs font-medium">3</button>
          <button className="w-6 h-6 rounded flex items-center justify-center text-muted-foreground hover:bg-[#30363d] transition-colors text-xs font-medium">4</button>
          <button className="w-6 h-6 rounded flex items-center justify-center text-muted-foreground hover:bg-[#30363d] transition-colors text-xs font-medium">5</button>
          <span className="px-1 text-muted-foreground text-xs">...</span>
          <button className="w-6 h-6 rounded flex items-center justify-center text-muted-foreground hover:bg-[#30363d] transition-colors text-xs font-medium">32</button>
          <button className="w-6 h-6 rounded flex items-center justify-center text-muted-foreground hover:bg-[#30363d] transition-colors text-xs font-medium">&gt;</button>
        </div>
        <span className="text-xs text-muted-foreground">Showing 1 to 8 of 1,248 documents</span>
      </div>

    </div>
  );
}
