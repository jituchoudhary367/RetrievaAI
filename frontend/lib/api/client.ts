import { ErrorDetail, ErrorResponse } from "../types/models";
import { getAuthToken, clearAuthToken } from "../auth/session";

export const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

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

export class AuthError extends ApiError {
  constructor(errors: ErrorDetail[], message?: string) {
    super(401, errors, message || "Authentication required");
    this.name = "AuthError";
  }
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${apiBaseUrl}${path}`;
  
  const headers = new Headers(init?.headers);
  if (!headers.has("Content-Type") && !(init?.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  // Inject JWT Token
  const token = getAuthToken();
  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  let response: Response;
  try {
    response = await fetch(url, { cache: "no-store", ...init, headers });
  } catch (networkErr: any) {
    // Connection refused, CORS failure, or offline
    throw new ApiError(0, [{ code: "NETWORK_ERROR", message: "Cannot reach the API server. Please make sure the backend is running." }], networkErr?.message || "Failed to fetch");
  }

  if (!response.ok) {
    let errorResponse: ErrorResponse | null = null;
    try {
      errorResponse = await response.json();
    } catch {
      // Not JSON
    }

    if (errorResponse && errorResponse.errors) {
      if (response.status === 401) {
        clearAuthToken();
        throw new AuthError(errorResponse.errors, response.statusText);
      }
      throw new ApiError(response.status, errorResponse.errors, response.statusText);
    }
    
    if (response.status === 401) {
      clearAuthToken();
      throw new AuthError([{ code: "UNAUTHORIZED", message: response.statusText }]);
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
