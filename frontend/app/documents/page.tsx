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
      quality: 0.93
    },
    {
      id: "doc4",
      type: "pdf",
      title: "Advanced Retrieval Techniques.pdf",
      tags: ["retrieval", "rerank", "techniques"],
      source: "/docs/retrieval",
      chunks: 512,
      size: "3.2 MB",
      uploaded: "May 21, 2024 03:20 PM",
      quality: 0.91
    },
    {
      id: "doc5",
      type: "md",
      title: "Qdrant Best Practices.md",
      tags: ["qdrant", "vector-db", "performance"],
      source: "/docs/qdrant",
      chunks: 221,
      size: "1.3 MB",
      uploaded: "May 20, 2024 09:10 AM",
      quality: 0.90
    },
    {
      id: "doc6",
      type: "txt",
      title: "Production RAG Checklist.txt",
      tags: ["checklist", "production", "deploy"],
      source: "/docs/ops",
      chunks: 58,
      size: "98 KB",
      uploaded: "May 19, 2024 06:33 PM",
      quality: 0.88
    },
    {
      id: "doc7",
      type: "code",
      title: "hybrid_retriever.py",
      tags: ["code", "retriever", "python"],
      source: "/src/retrieval",
      chunks: 0,
      size: "12 KB",
      uploaded: "May 19, 2024 05:11 PM",
      quality: null // No score for code in mockup
    },
    {
      id: "doc8",
      type: "pdf",
      title: "LangChain Integration Guide.pdf",
      tags: ["langchain", "integration", "guide"],
      source: "/docs/integration",
      chunks: 275,
      size: "2.1 MB",
      uploaded: "May 18, 2024 02:45 PM",
      quality: 0.94
    }
  ];

  const selectedDoc = selectedDocId ? mockDocuments.find(d => d.id === selectedDocId) : null;

  return (
    <div className="flex h-full w-full bg-background overflow-hidden">
      {/* Center Area (Table) */}
      <div className="flex-1 flex flex-col min-w-0 border-r border-border relative bg-background">
        <TopBar 
          title="Documents"
          subtitle="Manage and explore your knowledge base"
        />
        
        <div className="flex-1 overflow-y-auto scrollbar-thin flex flex-col items-center">
          <div className="w-full max-w-[1200px] p-6 lg:p-8 flex flex-col gap-6">
            <DocumentStatsRow />
            <DocumentListArea 
              documents={mockDocuments} 
              selectedDocId={selectedDocId}
              onSelectDoc={setSelectedDocId} 
            />
          </div>
        </div>
      </div>

      {/* Right Sidebar (Details) */}
      {selectedDoc && (
        <div className="w-96 flex-shrink-0 bg-[#0d1117] overflow-y-auto hidden lg:flex flex-col border-l border-[#30363d] animate-in slide-in-from-right-16 duration-300">
           <DocumentDetailPanel document={selectedDoc} onClose={() => setSelectedDocId(null)} />
        </div>
      )}
    </div>
  );
}
