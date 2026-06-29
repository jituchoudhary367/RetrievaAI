import { ErrorDetail, ErrorResponse } from "../types/models";

export const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export class ApiError extends Error {
  statusCode: number;
  errors: ErrorDetail[];

  constructor(statusCode: number, errors: ErrorDetail[], message?: string) {
    super(message || errors.map((e) => e.message).join(", ") || "Unknown API Error");
    this.name = "ApiError";
    this.statusCode = statusCode;
    this.errors = errors;
  }
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${apiBaseUrl}${path}`;
  
  const headers = new Headers(init?.headers);
  if (!headers.has("Content-Type") && !(init?.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  // Inject JWT Token
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("token");
    if (token && !headers.has("Authorization")) {
      headers.set("Authorization", `Bearer ${token}`);
    }
  }

  const response = await fetch(url, { ...init, headers });

  if (!response.ok) {
    let errorResponse: ErrorResponse | null = null;
    try {
      errorResponse = await response.json();
    } catch {
      // Not JSON
    }

    if (errorResponse && errorResponse.errors) {
      throw new ApiError(response.status, errorResponse.errors, response.statusText);
    }
    
    throw new ApiError(response.status, [{ code: "UNKNOWN", message: response.statusText }]);
  }

  // Handle empty responses
  const text = await response.text();
  if (!text) {
    return {} as T;
  }

  return JSON.parse(text) as T;
}
