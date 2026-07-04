"use client";

import React, { useState, useEffect, useCallback } from 'react';
import { TopBar } from '@/components/layout/TopBar';
import { DocumentStatsRow } from '@/components/documents/DocumentStatsRow';
import { DocumentListArea } from '@/components/documents/DocumentListArea';
import { DocumentDetailPanel } from '@/components/documents/DocumentDetailPanel';
import RequireAuth from '@/components/auth/RequireAuth';
import { documentsApi } from '@/lib/api/documents';
import { analyticsApi } from '@/lib/api/analytics';

export default function DocumentsPage() {
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);
  const [documents, setDocuments] = useState<any[]>([]);
  const [totalDocuments, setTotalDocuments] = useState(0);
  const [totalChunks, setTotalChunks] = useState(0);
  const [totalBytes, setTotalBytes] = useState(0);

  const fetchDocuments = useCallback(async () => {
    try {
      const docs = await documentsApi.listDocuments();
      const mapped = docs.map((doc: any) => ({
        id: doc.id,
        title: doc.file_name || doc.title || doc.source_path || 'Untitled',
        type: ((doc.file_name || doc.title || '').split('.').pop() || 'txt').toLowerCase(),
        size: doc.file_size_bytes ? `${(doc.file_size_bytes / 1024).toFixed(1)} KB` : 'Unknown',
        uploaded: doc.created_at ? new Date(doc.created_at).toLocaleString() : 'Unknown',
        status: doc.status || 'Indexed',
        source: doc.source_type || 'Document',
        author: 'System',
        chunks: doc.chunk_count || 0,
        tags: [],
        quality: null,
      }));
      setDocuments(mapped);
      setTotalDocuments(mapped.length);
      setTotalChunks(mapped.reduce((sum: number, d: any) => sum + (d.chunks || 0), 0));
      setTotalBytes(docs.reduce((sum: number, doc: any) => sum + (doc.file_size_bytes || 0), 0));
    } catch (err) {
      console.error('Failed to load documents:', err);
    }
  }, []);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  const selectedDoc = documents.find(d => d.id === selectedDocId);

  return (
    <RequireAuth>
      <div className="flex flex-col h-full bg-background relative overflow-hidden">
        <TopBar title="Documents" />
        <div className="flex flex-1 overflow-hidden">
          <div className="flex-1 flex flex-col min-w-0 border-r border-border bg-background p-4 overflow-y-auto space-y-4">
            <DocumentStatsRow
              totalDocuments={totalDocuments}
              totalChunks={totalChunks}
              storageUsedBytes={totalBytes}
            />
            <DocumentListArea documents={documents} selectedDocId={selectedDocId} onSelectDoc={setSelectedDocId} />
          </div>
          {selectedDoc && (
            <div className="w-80 flex-shrink-0 flex flex-col bg-muted/10 border-l border-border overflow-y-auto hidden lg:flex">
              <div className="flex-1 p-2 space-y-2">
                <DocumentDetailPanel 
                  document={selectedDoc} 
                  onClose={async (id?: string, shouldDelete?: boolean) => {
                    if (shouldDelete && id) {
                      try {
                        await documentsApi.deleteDocument(id);
                        await fetchDocuments();
                      } catch (e) {
                        console.error(e);
                        alert("Failed to delete document.");
                      }
                    }
                    setSelectedDocId(null);
                  }} 
                />
              </div>
            </div>
          )}
        </div>
      </div>
    </RequireAuth>
  );
}
