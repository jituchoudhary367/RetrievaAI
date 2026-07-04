import React, { useState, useEffect } from 'react';
import { X, FileText, Download, Trash2, Box } from 'lucide-react';
import { ingestionApi } from '../../lib/api/ingest';
import { apiBaseUrl } from '../../lib/api/client';

export function IngestionDetailPanel({ job, onClose }: any) {
  const [activeTab, setActiveTab] = useState('Overview');
  const tabs = ['Overview', 'Chunks', 'Metadata', 'Logs'];

  const [chunks, setChunks] = useState<any[]>([]);
  const [metadata, setMetadata] = useState<any>(null);
  const [logs, setLogs] = useState<any[]>([]);
  const [loadingChunks, setLoadingChunks] = useState(false);
  const [loadingMetadata, setLoadingMetadata] = useState(false);

  useEffect(() => {
    // Reset state when job changes
    setChunks([]);
    setMetadata(null);
    setLogs([]);
    setActiveTab('Overview');
  }, [job?.id]);

  useEffect(() => {
    if (!job?.id) return;
    
    if (activeTab === 'Chunks' && chunks.length === 0) {
      setLoadingChunks(true);
      ingestionApi.getJobChunks(job.id)
        .then(setChunks)
        .catch(console.error)
        .finally(() => setLoadingChunks(false));
    }
    
    if (activeTab === 'Metadata' && !metadata) {
      setLoadingMetadata(true);
      ingestionApi.getJobMetadata(job.id)
        .then(setMetadata)
        .catch(console.error)
        .finally(() => setLoadingMetadata(false));
    }

    if (activeTab === 'Logs') {
      const eventSource = new EventSource(`${apiBaseUrl}/api/ingestion/jobs/${job.id}/stream`);
      
      eventSource.onmessage = (event) => {
        try {
          if (event.data === "ping") return;
          const parsed = JSON.parse(event.data);
          setLogs(prev => [...prev, parsed]);
        } catch (e) {}
      };

      eventSource.onerror = () => {
        eventSource.close();
      };

      return () => {
        eventSource.close();
      };
    }
  }, [activeTab, job?.id]);

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
        <button onClick={() => onClose()} className="text-muted-foreground hover:text-foreground transition-colors flex-shrink-0">
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
        
        {activeTab === 'Overview' && (
          <>
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
                <span className="text-[10px] text-foreground">{job.subtitle?.includes('•') ? job.subtitle.split('•')[0].trim() : 'N/A'}</span>
              </div>
              <div className="flex items-center justify-between border-b border-[#1e2329] pb-2">
                <span className="text-[10px] text-muted-foreground">Pages</span>
                <span className="text-[10px] text-foreground">{job.subtitle?.includes('•') ? (job.subtitle.split('•')[1]?.trim().split(' ')[0] || '-') : '-'}</span>
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
                <span className="text-[10px] text-foreground">{job.durationMs ? `${(job.durationMs / 1000).toFixed(1)}s` : 'N/A'}</span>
              </div>
            </div>
          </>
        )}

        {activeTab === 'Chunks' && (
          <div className="flex flex-col space-y-4">
            {loadingChunks ? (
              <div className="text-xs text-muted-foreground text-center py-8">Loading chunks...</div>
            ) : chunks.length === 0 ? (
              <div className="text-xs text-muted-foreground text-center py-8">No chunks available.</div>
            ) : (
              chunks.map((chunk, i) => (
                <div key={i} className="bg-[#12181f] border border-[#1e2329] rounded-lg p-3 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] text-muted-foreground font-mono">Chunk {chunk.chunk_index || i+1}</span>
                    <span className="text-[9px] text-muted-foreground">{chunk.text.length} chars</span>
                  </div>
                  <p className="text-xs text-foreground line-clamp-3">{chunk.text}</p>
                </div>
              ))
            )}
          </div>
        )}

        {activeTab === 'Metadata' && (
          <div className="flex flex-col space-y-4">
            {loadingMetadata ? (
              <div className="text-xs text-muted-foreground text-center py-8">Loading metadata...</div>
            ) : !metadata || Object.keys(metadata).length === 0 ? (
              <div className="text-xs text-muted-foreground text-center py-8">No metadata available.</div>
            ) : (
              <div className="bg-[#12181f] border border-[#1e2329] rounded-lg p-4 space-y-3">
                {Object.entries(metadata).map(([key, value]: [string, any]) => (
                  <div key={key} className="flex flex-col space-y-1 border-b border-[#1e2329] pb-2 last:border-0 last:pb-0">
                    <span className="text-[10px] text-muted-foreground font-medium uppercase tracking-wider">{key}</span>
                    <span className="text-xs text-foreground font-mono break-all">
                      {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'Logs' && (
          <div className="flex flex-col bg-[#0d1117] border border-[#1e2329] rounded-lg p-3 h-[400px] overflow-y-auto font-mono text-[10px]">
            {logs.length === 0 ? (
              <span className="text-muted-foreground text-center py-4">Waiting for logs...</span>
            ) : (
              logs.map((log, i) => (
                <div key={i} className="flex space-x-2 py-1">
                  <span className="text-[#3b82f6] shrink-0">[{log.timestamp ? new Date(log.timestamp).toLocaleTimeString() : 'TIME'}]</span>
                  <span className={`shrink-0 ${log.level === 'ERROR' ? 'text-red-500' : 'text-muted-foreground'}`}>[{log.level}]</span>
                  <span className={log.level === 'ERROR' ? 'text-red-400' : 'text-foreground'}>{log.message}</span>
                </div>
              ))
            )}
          </div>
        )}

      </div>

      {/* Footer Buttons Fixed */}
      <div className="absolute bottom-0 left-0 right-0 p-4 bg-[#0d1117] border-t border-[#30363d] flex items-center justify-between space-x-2">
        <button 
          onClick={async () => {
            if (confirm("Are you sure you want to delete this job and its ingested data?")) {
              if (onClose) onClose(job.id, true);
            }
          }}
          className="flex-1 flex items-center justify-center space-x-1 py-1.5 rounded border border-red-500/50 text-red-500 hover:bg-red-500/10 transition-colors text-[10px] font-medium"
        >
          <Trash2 className="h-3 w-3" />
          <span>Delete</span>
        </button>
      </div>

    </div>
  );
}
