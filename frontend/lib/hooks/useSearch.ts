import { useState, useCallback } from "react";
import { SearchRequest, SearchResult } from "../types/models";
import { postSearch } from "../api/search";

export function useSearch() {
  const [results, setResults] = useState<SearchResult[]>([]);
  const [debugInfo, setDebugInfo] = useState<Record<string, any> | undefined>(undefined);
  const [latencyMs, setLatencyMs] = useState<number>(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const search = useCallback(async (request: SearchRequest) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await postSearch(request);
      setResults(response.results);
      setDebugInfo(response.debugInfo);
      setLatencyMs(response.latencyMs);
    } catch (err: any) {
      setError(err.message || "An error occurred during search.");
      setResults([]);
      setDebugInfo(undefined);
      setLatencyMs(0);
    } finally {
      setIsLoading(false);
    }
  }, []);

  return { results, debugInfo, latencyMs, search, isLoading, error };
}
