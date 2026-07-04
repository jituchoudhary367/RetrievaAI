import { ChatResponse, QueryRequest, StreamChunk } from "../types/models";
import { apiBaseUrl, ApiError, apiFetch } from "./client";
import { parseSseStream } from "../utils/sse";
import { getAuthToken } from "../auth/session";

export async function postQuery(request: QueryRequest): Promise<ChatResponse> {
  const req = { ...request, stream: false };
  return apiFetch<ChatResponse>("/api/query", {
    method: "POST",
    body: JSON.stringify(req),
  });
}

export async function streamQuery(
  request: QueryRequest,
  onChunk: (c: StreamChunk) => void,
  signal?: AbortSignal
): Promise<void> {
  const req = { ...request, stream: true };
  const url = `${apiBaseUrl}/api/stream`;

  const token = getAuthToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(url, {
    method: "POST",
    headers,
    body: JSON.stringify(req),
    signal,
  });

  if (!response.ok) {
    let errorData = null;
    try {
      errorData = await response.json();
    } catch {
      // Ignore
    }
    
    if (errorData && errorData.errors) {
      throw new ApiError(response.status, errorData.errors, response.statusText);
    }
    throw new ApiError(response.status, [{ code: "UNKNOWN", message: response.statusText }]);
  }

  await parseSseStream(response, onChunk);
}

export async function getSuggestedQuestions(): Promise<string[]> {
  return apiFetch<string[]>("/api/suggest-questions", {
    method: "GET",
  });
}

