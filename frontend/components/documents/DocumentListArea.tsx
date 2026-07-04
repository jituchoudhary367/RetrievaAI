"use client";

import React, { useState, useEffect } from 'react';
import { Search, FileText, Code, Eye, Download, MoreVertical, LayoutGrid, List } from 'lucide-react';

export function DocumentListArea({ documents, selectedDocId, onSelectDoc }: any) {
  const [searchQuery, setSearchQuery] = useState("");
  const [sortOption, setSortOption] = useState("Newest First");
  const [viewMode, setViewMode] = useState("list");
  const [showSortDropdown, setShowSortDropdown] = useState(false);

  useEffect(() => {
    const savedSort = localStorage.getItem("docSortOption");
    if (savedSort) setSortOption(savedSort);
    const savedView = localStorage.getItem("docViewMode");
    if (savedView) setViewMode(savedView);
  }, []);

  const handleSortChange = (opt: string) => {
    setSortOption(opt);
    localStorage.setItem("docSortOption", opt);
    setShowSortDropdown(false);
  };

  const handleViewChange = (mode: string) => {
    setViewMode(mode);
    localStorage.setItem("docViewMode", mode);
  };

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

  const parseSize = (sizeStr: string) => {
    if (!sizeStr || sizeStr === 'Unknown') return 0;
    const val = parseFloat(sizeStr);
    if (sizeStr.includes('MB')) return val * 1024;
    return val;
  };

  const sortDocuments = (docs: any[]) => {
    return [...docs].sort((a, b) => {
      switch (sortOption) {
        case "Newest First":
          return new Date(b.uploaded).getTime() - new Date(a.uploaded).getTime();
        case "Oldest First":
          return new Date(a.uploaded).getTime() - new Date(b.uploaded).getTime();
        case "Name A-Z":
          return (a.title || "").localeCompare(b.title || "");
        case "Name Z-A":
          return (b.title || "").localeCompare(a.title || "");
        case "Size (Largest)":
          return parseSize(b.size) - parseSize(a.size);
        case "Size (Smallest)":
          return parseSize(a.size) - parseSize(b.size);
        default:
          return 0;
      }
    });
  };

  const filteredDocuments = sortDocuments(documents.filter((doc: any) => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      doc.title?.toLowerCase().includes(query) ||
      doc.source?.toLowerCase().includes(query) ||
      doc.tags?.some((t: string) => t.toLowerCase().includes(query))
    );
  }));

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
        </div>

        {/* Right side controls */}
        <div className="flex items-center space-x-4 w-full md:w-auto justify-end relative">
          <div 
            className="flex items-center text-xs text-muted-foreground space-x-1 cursor-pointer hover:text-foreground relative"
            onClick={() => setShowSortDropdown(!showSortDropdown)}
          >
            <span>Sort:</span>
            <span className="font-medium text-foreground">{sortOption}</span>
            <span className="ml-1 text-[10px]">⌄</span>
          </div>
          
          {showSortDropdown && (
            <div className="absolute top-full right-16 mt-1 z-50 bg-[#12181f] border border-[#30363d] rounded-md shadow-xl py-1 w-36">
              {["Newest First", "Oldest First", "Name A-Z", "Name Z-A", "Size (Largest)", "Size (Smallest)"].map(opt => (
                <button 
                  key={opt}
                  className={`block w-full text-left px-3 py-1.5 text-xs ${sortOption === opt ? 'text-[#10b981] bg-[#1a212a]' : 'text-muted-foreground hover:text-foreground hover:bg-[#1a212a]'}`}
                  onClick={() => handleSortChange(opt)}
                >
                  {opt}
                </button>
              ))}
            </div>
          )}

          <div className="flex items-center border border-[#30363d] rounded-md overflow-hidden">
            <button 
              className={`p-1.5 transition-colors ${viewMode === 'list' ? 'bg-[#122822] text-[#10b981]' : 'bg-transparent text-muted-foreground hover:text-foreground hover:bg-[#30363d]/50'}`}
              onClick={() => handleViewChange('list')}
            >
              <List className="h-4 w-4" />
            </button>
            <button 
              className={`p-1.5 transition-colors ${viewMode === 'grid' ? 'bg-[#122822] text-[#10b981]' : 'bg-transparent text-muted-foreground hover:text-foreground hover:bg-[#30363d]/50'}`}
              onClick={() => handleViewChange('grid')}
            >
              <LayoutGrid className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>

      {filteredDocuments.length === 0 ? (
        <div className="px-4 py-10 text-center text-muted-foreground text-xs border border-[#1e2329] rounded-lg bg-[#0d1117]/50">
          {searchQuery ? `No documents match "${searchQuery}"` : 'No documents uploaded yet'}
        </div>
      ) : (
        <>
          {viewMode === 'list' ? (
            /* Table View */
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
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#1e2329]">
                  {filteredDocuments.map((doc: any) => (
                    <tr 
                      key={doc.id} 
                      onClick={() => onSelectDoc(doc.id)}
                      className={`group transition-colors cursor-pointer ${
                        selectedDocId === doc.id ? 'bg-[#161b22] border-l-2 border-l-[#10b981]' : 'hover:bg-[#12181f] border-l-2 border-l-transparent'
                      }`}
                    >
                      <td className="px-4 py-3 min-w-[280px]">
                        <div className="flex items-start space-x-3">
                          <div className="mt-0.5">{getIcon(doc.type)}</div>
                          <div className="flex flex-col space-y-1">
                            <span className="text-sm font-semibold text-foreground group-hover:text-primary transition-colors">
                              {doc.title}
                            </span>
                            <div className="flex flex-wrap gap-1 mt-0.5">
                              {doc.tags?.map((tag: string) => (
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
                          <span>{doc.uploaded}</span>
                        </div>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap font-medium">
                        <span className={getScoreColor(doc.quality)}>
                          {doc.quality !== null ? doc.quality.toFixed(2) : '-'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            /* Grid View */
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-4">
              {filteredDocuments.map((doc: any) => (
                <div
                  key={doc.id}
                  onClick={() => onSelectDoc(doc.id)}
                  className={`flex flex-col p-4 rounded-lg border cursor-pointer transition-colors ${
                    selectedDocId === doc.id ? 'bg-[#161b22] border-[#10b981]' : 'bg-[#0d1117]/50 border-[#1e2329] hover:bg-[#12181f] hover:border-[#30363d]'
                  }`}
                >
                  <div className="flex items-start space-x-3 mb-3">
                    <div className="flex-shrink-0">{getIcon(doc.type)}</div>
                    <div className="flex flex-col flex-1 min-w-0">
                      <span className="text-sm font-semibold text-foreground truncate" title={doc.title}>{doc.title}</span>
                      <span className="text-[10px] text-muted-foreground truncate">{doc.source}</span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between mt-auto pt-3 border-t border-[#1e2329] text-[10px] text-muted-foreground">
                    <span>{doc.size}</span>
                    <span>{doc.chunks} chunks</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {/* Pagination Footer - Only show if there are documents */}
      {documents.length > 0 && (
        <div className="flex items-center justify-between mt-6 px-1">
          {documents.length > 10 ? (
            <div className="flex items-center space-x-1">
              <button className="w-6 h-6 rounded flex items-center justify-center text-muted-foreground hover:bg-[#30363d] transition-colors text-xs font-medium">&lt;</button>
              <button className="w-6 h-6 rounded flex items-center justify-center bg-[#10b981] text-background text-xs font-medium">1</button>
              <button className="w-6 h-6 rounded flex items-center justify-center text-muted-foreground hover:bg-[#30363d] transition-colors text-xs font-medium">&gt;</button>
            </div>
          ) : (
            <div></div> /* Empty div to push text to the right if no pagination */
          )}
          <span className="text-xs text-muted-foreground">Showing {filteredDocuments.length} of {documents.length} documents</span>
        </div>
      )}

    </div>
  );
}
