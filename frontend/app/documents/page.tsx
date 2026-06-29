"use client";

import React, { useState, useEffect } from 'react';
import { TopBar } from '../../components/layout/TopBar';
import { DocumentStatsRow } from '../../components/documents/DocumentStatsRow';
import { DocumentListArea } from '../../components/documents/DocumentListArea';
import { DocumentDetailPanel } from '../../components/documents/DocumentDetailPanel';
import { documentsApi } from '../../lib/api/documents';
import { DocumentRow } from '../../lib/types/backend';

export default function DocumentsPage() {
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);
  const [documents, setDocuments] = useState<DocumentRow[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadDocs() {
      try {
        const docs = await documentsApi.listDocuments();
        setDocuments(docs);
      } catch (err) {
        console.error("Failed to load documents", err);
      } finally {
        setLoading(false);
      }
    }
    loadDocs();
  }, []);

  const selectedDoc = selectedDocId ? documents.find(d => d.id === selectedDocId) : null;

  return (
    <div className="flex flex-col h-full w-full bg-background overflow-hidden">
      <TopBar 
        title="Documents"
        subtitle="Manage and view all indexed documents in your knowledge base"
      />
      <div className="flex-1 flex min-h-0">
        {/* Center Area (List) */}
        <div className="flex-1 overflow-y-auto scrollbar-thin bg-background relative">
          <div className="flex flex-col p-6 lg:p-8 gap-6 max-w-[1200px] mx-auto w-full">
            <DocumentStatsRow />
            {loading ? (
              <div className="flex justify-center items-center h-64 text-muted-foreground">Loading documents...</div>
            ) : (
              <DocumentListArea 
                documents={documents} 
                selectedDocId={selectedDocId} 
                onSelectDoc={setSelectedDocId} 
              />
            )}
          </div>
        </div>

        {/* Right Sidebar (Details) */}
        {selectedDoc && (
          <div className="w-80 lg:w-[380px] flex-shrink-0 bg-[#0d1117] overflow-y-auto hidden md:flex flex-col border-l border-[#30363d] animate-in slide-in-from-right-16 duration-300">
             <DocumentDetailPanel document={selectedDoc} onClose={() => setSelectedDocId(null)} />
          </div>
        )}
      </div>
    </div>
  );
}
