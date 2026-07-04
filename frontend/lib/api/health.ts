import { HealthResponse } from "../types/models";
import { apiFetch } from "./client";

// NOTE: These endpoints must hit the root paths (/health, /ready, /live) 
// and NOT /api/health per the backend contract.
export async function getHealth(): Promise<HealthResponse> {
  return apiFetch<HealthResponse>("/api/health/live");
}

export async function getReady(): Promise<HealthResponse> {
  return apiFetch<HealthResponse>("/api/health/ready");
}

export async function getLive(): Promise<HealthResponse> {
  return apiFetch<HealthResponse>("/api/health/live");
}
