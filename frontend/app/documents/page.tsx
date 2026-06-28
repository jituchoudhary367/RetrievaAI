"use client";

import React, { useState } from 'react';
import { TopBar } from '../../components/layout/TopBar';
import { DocumentStatsRow } from '../../components/documents/DocumentStatsRow';
import { DocumentListArea } from '../../components/documents/DocumentListArea';
import { DocumentDetailPanel } from '../../components/documents/DocumentDetailPanel';

export default function DocumentsPage() {
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);

  // Hardcoded visual mock data based on screenshot
  const mockDocuments = [
    {
      id: "doc1",
      type: "pdf",
      title: "RAG System Architecture Overview.pdf",
      tags: ["architecture", "rag", "overview"],
      source: "/docs/architecture",
      chunks: 245,
      size: "2.4 MB",
      uploaded: "May 24, 2024 10:30 AM",
      quality: 0.98,
      pages: 28,
      words: "8,532",
      tokens: "12,845",
      uploader: "Admin User",
      checksum: "a4f9c2e7bd1f3a6...",
      description: "High-level overview of the production RAG system architecture including components, data flow, and technology stack."
    },
    {
      id: "doc2",
      type: "md",
      title: "Hybrid Search in Production RAG.md",
      tags: ["hybrid-search", "bm25", "dense"],
      source: "/docs/search",
      chunks: 342,
      size: "1.8 MB",
      uploaded: "May 23, 2024 04:15 PM",
      quality: 0.95
    },
    {
      id: "doc3",
      type: "ppt",
      title: "RAG Pipeline Deep Dive.pptx",
      tags: ["pipeline", "rag", "presentation"],
      source: "/docs/pipeline",
      chunks: 186,
      size: "5.7 MB",
      uploaded: "May 22, 2024 11:42 AM",
      type: "md",
      title: "RAG Pipeline Deep Dive.md",
      quality: 92,
      source: "GitHub Integration",
      tags: ["pipeline", "technical", "docs"],
      date: "May 22, 2024",
      size: "85 KB"
    },
    {
      id: "doc4",
      type: "pptx",
      title: "Advanced Retrieval Techniques.pptx",
      quality: 88,
      source: "Confluence",
      tags: ["retrieval", "presentation"],
      date: "May 20, 2024",
      size: "5.7 MB"
    },
    {
      id: "doc5",
      type: "csv",
      title: "Product QA Dataset.csv",
      quality: 100,
      source: "S3 Bucket",
      tags: ["dataset", "testing", "qa"],
      date: "May 19, 2024",
      size: "2.1 MB"
    }
  ];

  const selectedDoc = selectedDocId ? mockDocuments.find(d => d.id === selectedDocId) : null;

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
            <DocumentListArea 
              documents={mockDocuments} 
              selectedDocId={selectedDocId} 
              onSelectDoc={setSelectedDocId} 
            />
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
