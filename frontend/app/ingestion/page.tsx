"use client";

import React, { useState } from 'react';
import { TopBar } from '../../components/layout/TopBar';
import { IngestionStatsRow } from '../../components/ingestion/IngestionStatsRow';
import { IngestionUploadArea } from '../../components/ingestion/IngestionUploadArea';
import { IngestionConfigArea } from '../../components/ingestion/IngestionConfigArea';
import { IngestionListArea } from '../../components/ingestion/IngestionListArea';
import { IngestionDetailPanel } from '../../components/ingestion/IngestionDetailPanel';

export default function IngestionPage() {
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);

  // Hardcoded visual mock data based on screenshot
  const mockJobs = [
    {
      id: "job1",
      type: "pdf",
      title: "RAG System Architecture Overview.pdf",
      subtitle: "2.4 MB • 24 pages",
      source: "/docs/architecture",
      status: "Completed",
      progress: 100,
      chunks: "245",
      indexed: "245",
      started: "May 24, 10:30 AM",
      uploader: "Admin User",
      processingTime: "38s",
      model: "bge-large-en-v1.5",
      parser: "Unstructured PDF",
      chunkSize: "1024 tokens",
      chunkOverlap: "200 tokens"
    },
    {
      id: "job2",
      type: "docx",
      title: "Hybrid Search in Production RAG.docx",
      subtitle: "1.8 MB • 18 pages",
      source: "/docs/search",
      status: "Completed",
      progress: 100,
      chunks: "342",
      indexed: "342",
      started: "May 23, 04:15 PM"
    },
    {
      id: "job3",
      type: "md",
      title: "RAG Pipeline Deep Dive.md",
      subtitle: "85 KB • 12 pages",
      source: "/docs/pipeline",
      status: "Processing",
      progress: 68,
      chunks: "186",
      indexed: "126",
      started: "May 25, 11:20 AM"
    },
    {
      id: "job4",
      type: "pptx",
      title: "Advanced Retrieval Techniques.pptx",
      subtitle: "5.7 MB • 42 slides",
      source: "/docs/retrieval",
      status: "Queued",
      progress: 0,
      chunks: "-",
      indexed: "-",
      started: "May 25, 11:45 AM"
    },
    {
      id: "job5",
      type: "csv",
      title: "Product QA Dataset.csv",
      subtitle: "2.1 MB • 3,245 rows",
      source: "/data/datasets",
      status: "Completed",
      progress: 100,
      chunks: "1,245",
      indexed: "1,245",
      started: "May 22, 09:10 AM"
    },
    {
      id: "job6",
      type: "zip",
      title: "Scanned Document Images (120).zip",
      subtitle: "12.3 MB • 120 files",
      source: "/docs/scanned",
      status: "Failed",
      progress: 0,
      chunks: "0",
      indexed: "0",
      started: "May 21, 03:33 PM"
    }
  ];

  const selectedJob = selectedJobId ? mockJobs.find(j => j.id === selectedJobId) : null;

  return (
    <div className="flex flex-col h-full w-full bg-background overflow-hidden">
      <TopBar 
        title="Ingestion"
        subtitle="Upload, process and index documents into your knowledge base"
      />
      <div className="flex-1 flex min-h-0">
        {/* Center Area (Upload + List) */}
        <div className="flex-1 overflow-y-auto scrollbar-thin bg-background relative">
          <div className="flex flex-col p-6 lg:p-8 gap-6 max-w-[1200px] mx-auto w-full">
            <IngestionStatsRow />
            
            <div className="flex flex-col space-y-4">
              <IngestionUploadArea />
              <IngestionConfigArea />
            </div>

            <IngestionListArea 
              jobs={mockJobs} 
              selectedJobId={selectedJobId}
              onSelectJob={setSelectedJobId} 
            />
          </div>
        </div>

        {/* Right Sidebar (Details) */}
        {selectedJob && (
          <div className="w-80 flex-shrink-0 bg-[#0d1117] overflow-y-auto hidden lg:flex flex-col border-l border-[#30363d] animate-in slide-in-from-right-16 duration-300">
             <IngestionDetailPanel job={selectedJob} onClose={() => setSelectedJobId(null)} />
          </div>
        )}
      </div>
    </div>
  );
}
