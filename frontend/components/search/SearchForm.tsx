"use client";

import React, { useState } from "react";
import { useSearch } from "../../lib/hooks/useSearch";
import { FilterBuilder } from "./FilterBuilder";
import { ResultCard } from "./ResultCard";
import { MetadataFilter } from "../../lib/types/models";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Spinner } from "../ui/spinner";
import { Search } from "lucide-react";

export function SearchForm() {
  const { search, results, isLoading, error, latencyMs, debugInfo } = useSearch();
  const [query, setQuery] = useState("");
  const [filters, setFilters] = useState<MetadataFilter[]>([]);
  const [topK, setTopK] = useState(10);
  const [rerank, setRerank] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      search({
        query: query.trim(),
        filters: filters.length > 0 ? filters : undefined,
        topK,
        rerank,
        includeDebugInfo: true,
      });
    }
  };

  return (
    <div className="flex flex-col gap-6 md:flex-row">
      {/* Sidebar Controls */}
      <div className="w-full md:w-80 shrink-0 space-y-6">
        <form onSubmit={handleSubmit} className="space-y-4 rounded-xl border bg-card p-5 shadow-sm">
          <div className="space-y-2">
            <label htmlFor="query" className="text-sm font-medium">Search Query</label>
            <div className="relative">
              <Input
                id="query"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="What are you looking for?"
                className="pr-10"
              />
              <Search className="absolute right-3 top-2.5 h-4 w-4 text-muted-foreground" />
            </div>
          </div>
          
          <FilterBuilder filters={filters} onChange={setFilters} />

          <div className="space-y-3 pt-2">
            <div className="flex items-center justify-between">
              <label htmlFor="topK" className="text-sm font-medium">Top K ({topK})</label>
              <input
                id="topK"
                type="range"
                min={1}
                max={50}
                value={topK}
                onChange={(e) => setTopK(parseInt(e.target.value))}
                className="w-32"
              />
            </div>
            
            <label className="flex items-center gap-2 text-sm font-medium cursor-pointer">
              <input
                type="checkbox"
                checked={rerank}
                onChange={(e) => setRerank(e.target.checked)}
                className="rounded border-input text-primary focus:ring-primary"
              />
              Enable Cross-Encoder Reranking
            </label>
          </div>

          <Button type="submit" className="w-full mt-2" disabled={isLoading || !query.trim()}>
            {isLoading ? <Spinner size="sm" className="mr-2" /> : null}
            Execute Search
          </Button>
        </form>

        {debugInfo && (
          <div className="rounded-xl border bg-muted/20 p-5 text-xs font-mono text-muted-foreground overflow-x-auto">
            <h4 className="font-semibold mb-2 uppercase text-[10px] tracking-wider text-foreground">Debug Info</h4>
            <pre>{JSON.stringify(debugInfo, null, 2)}</pre>
          </div>
        )}
      </div>

      {/* Results Area */}
      <div className="flex-1 space-y-4">
        <div className="flex items-center justify-between border-b pb-2">
          <h2 className="text-xl font-semibold tracking-tight">Results</h2>
          {results.length > 0 && (
            <div className="text-sm text-muted-foreground">
              Found {results.length} chunks in {latencyMs}ms
            </div>
          )}
        </div>

        {error && (
          <div className="rounded-md bg-destructive/10 p-4 text-sm text-destructive">
            <strong>Error: </strong> {error}
          </div>
        )}

        {isLoading ? (
          <div className="flex justify-center p-12">
            <Spinner size="lg" className="text-muted-foreground" />
          </div>
        ) : results.length === 0 && !error ? (
          <div className="flex h-40 items-center justify-center rounded-xl border border-dashed text-sm text-muted-foreground">
            No results yet. Run a search to see chunks here.
          </div>
        ) : (
          <div className="space-y-4">
            {results.map((res, i) => (
              <ResultCard key={`${res.chunkId}-${i}`} result={res} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
