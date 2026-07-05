"use client";

import { Suspense } from "react";

import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import { TopBar } from '@/components/layout/TopBar';
import { SearchInputArea } from '@/components/search/SearchInputArea';
import { AdvancedResultCard } from '@/components/search/AdvancedResultCard';
import { SearchFiltersPanel } from '@/components/search/SearchFiltersPanel';

import { SearchResult, SearchRequest } from '@/lib/types/models';
import RequireAuth from '@/components/auth/RequireAuth';
import { useSearch } from '@/lib/hooks/useSearch';

export const dynamic = "force-dynamic";

function SearchPageContent() {
  const searchParams = useSearchParams();
  const q = searchParams.get('q');
  
  const [query, setQuery] = useState(q || "");
  const [activeTab, setActiveTab] = useState("All Results");
  const { results, search, isLoading, latencyMs, debugInfo } = useSearch();

  // Trigger search on mount if 'q' is present
  useEffect(() => {
    if (q) {
      search({ query: q });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [q]);

  const handleSearch = () => {
    if (query.trim()) {
      search({ query });
    }
  };

  return (
    <RequireAuth>
      <div className="flex flex-col h-full bg-background relative overflow-hidden">
        <TopBar title="Search" />
        <div className="flex flex-1 overflow-hidden">
          <div className="flex-1 flex flex-col min-w-0 border-r border-border bg-background p-4 overflow-y-auto space-y-4">
            <SearchInputArea 
              query={query} 
              setQuery={setQuery} 
              onSearch={handleSearch} 
              isLoading={isLoading} 
              activeTab={activeTab}
              onTabChange={setActiveTab}
            />
            <div className="space-y-4">
              {results.map((r, i) => <AdvancedResultCard key={i} result={r} index={String(i)} />)}
              {results.length === 0 && !isLoading && (
                <div className="flex flex-col items-center justify-center p-16 space-y-4">
                  <div className="text-muted-foreground text-sm">
                    {activeTab === "Documents" && "No documents found."}
                    {activeTab === "Code" && "No code found."}
                    {activeTab === "Web" && "No web results found."}
                    {activeTab === "Knowledge Base" && "No knowledge base results found."}
                    {activeTab === "All Results" && "No results found."}
                  </div>
                </div>
              )}
            </div>
          </div>
          <div className="w-80 flex-shrink-0 flex flex-col bg-muted/10 overflow-y-auto hidden lg:flex">
            <div className="flex-1 p-2 space-y-2">
              <SearchFiltersPanel />
            </div>
          </div>
        </div>
      </div>
    </RequireAuth>
  );
}

export default function SearchPage() {
  return (
    <Suspense fallback={<div className="flex min-h-screen items-center justify-center">Loading...</div>}>
      <SearchPageContent />
    </Suspense>
  );
}
