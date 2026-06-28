import { SearchRequest, SearchResponse } from "../types/models";
import { apiFetch } from "./client";

export async function postSearch(request: SearchRequest): Promise<SearchResponse> {
  return apiFetch<SearchResponse>("/api/search", {
    method: "POST",
    body: JSON.stringify(request),
  });
}
