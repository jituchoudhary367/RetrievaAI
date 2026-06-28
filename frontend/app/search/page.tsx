"use client";

import React, { useState } from 'react';
import { TopBar } from '../../components/layout/TopBar';
import { SearchInputArea } from '../../components/search/SearchInputArea';
import { AdvancedResultCard } from '../../components/search/AdvancedResultCard';
import { SearchFiltersPanel } from '../../components/search/SearchFiltersPanel';
import { SearchAnalyticsPanel } from '../../components/search/SearchAnalyticsPanel';
import { SearchResult } from '../../lib/types/models';

export default function SearchPage() {
  const [query, setQuery] = useState("hybrid search in RAG systems");
  
  // Dummy results array for visual mock up based on screenshot
  const mockResults = [
    {
      id: "1",
      title: "Hybrid Search in Production RAG Systems",
      score: 0.98,
      type: "pdf",
      subtitle: "Page 12 • 98% relevant • production_rag_guide.pdf",
      snippet: "... <b>Hybrid search</b> combines dense vector similarity (semantic search) with sparse keyword matching (BM25) to overcome the limitations of both approaches. It significantly improves recall while...",
      matches: "hybrid search, RAG systems, BM25, dense, sparse, production",
    },
    {
      id: "2",
      title: "Implementing Hybrid Search with Qdrant + BM25",
      score: 0.95,
      type: "md",
      subtitle: "Section 2.1 • 95% relevant • huggingface_rag_blog.md",
      snippet: "... In our RAG pipeline, we use Reciprocal Rank Fusion (RRF) to merge results from Qdrant (dense vectors) and BM25 (sparse) retrievers. This ensures balanced relevance and better coverage...",
      matches: "hybrid search, Qdrant, BM25, RRF, retriever",
    },
    {
      id: "2_alt",
      title: "RAG System Architecture Overview",
      score: 0.92,
      type: "pdf",
      subtitle: "Page 7 • 92% relevant • rag_overview.pdf",
      snippet: "... The retrieval layer uses <b>hybrid search</b> to maximize the probability of retrieving all relevant chunks. Dense embeddings capture semantics while BM25 captures exact keyword matches...",
      matches: "retrieval layer, hybrid search, dense, BM25, architecture",
    },
    {
      id: "3",
      title: "Advanced Retrieval Techniques",
      score: 0.89,
      type: "pdf",
      subtitle: "Page 18 • 89% relevant • langchain_documentation.pdf",
      snippet: "... <b>Hybrid search</b> can be further enhanced with query expansion, reranking, and metadata filtering. It is the recommended approach for enterprise-grade RAG applications...",
      matches: "hybrid search, reranking, metadata filtering, enterprise",
    },
    {
      id: "5",
      title: "hybrid_retriever.py",
      score: 0.85,
      type: "code",
      subtitle: "Code • 85% relevant • github.com/your-org/rag-system",
      snippet: "class HybridRetriever:\n    \"\"\"Hybrid retriever combining dense vector search with BM25 sparse retrieval.\"\"\"",
      matches: "HybridRetriever, dense vector search, BM25",
    }
  ];

  return (
    <div className="flex h-full w-full bg-background overflow-hidden">
      {/* Left Area (Search Results) */}
      <div className="flex-1 flex flex-col min-w-0 border-r border-border relative">
        <TopBar 
          title="Search"
          subtitle="Find relevant information across your knowledge base"
        />
        
        <div className="flex-1 overflow-y-auto scrollbar-thin flex flex-col items-center">
          <div className="w-full max-w-4xl p-6 lg:p-8 flex flex-col gap-6">
            <SearchInputArea query={query} setQuery={setQuery} />
            
            <div className="flex flex-col gap-4 pb-12">
              {mockResults.map((res, idx) => (
                <AdvancedResultCard key={res.id} result={res} index={res.id} />
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Right Area (Filters & Analytics) */}
      <div className="w-80 flex-shrink-0 bg-[#0d1117] overflow-y-auto hidden lg:flex flex-col border-l border-[#30363d]">
         <SearchFiltersPanel />
         <SearchAnalyticsPanel />
      </div>
    </div>
  );
}
