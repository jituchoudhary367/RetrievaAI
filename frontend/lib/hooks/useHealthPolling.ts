import { useState, useEffect } from "react";
import { HealthResponse, ComponentHealth, HealthStatus } from "../types/models";
import { getReady } from "../api/health";

export function useHealthPolling(initialIntervalMs: number = 10000) {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [lastCheckedAt, setLastCheckedAt] = useState<Date | null>(null);

  useEffect(() => {
    let timeoutId: ReturnType<typeof setTimeout>;
    let isMounted = true;
    let currentInterval = initialIntervalMs;

    const checkHealth = async () => {
      // Pause polling if tab is not visible
      if (document.hidden) {
        if (isMounted) timeoutId = setTimeout(checkHealth, currentInterval);
        return;
      }

      try {
        const data: any = await getReady();
        if (isMounted) {
          // The backend returns components as a dictionary: { "redis": "ok", "qdrant": "ok" }
          // We need to map it to ComponentHealth[]
          const componentsList: ComponentHealth[] = [];
          if (data.components) {
            for (const [name, statusStr] of Object.entries(data.components)) {
              componentsList.push({
                name,
                status: (statusStr === "ok" ? "healthy" : statusStr === "down" ? "unhealthy" : "degraded") as HealthStatus,
                detail: String(statusStr)
              });
            }
          }

          const adaptedData: HealthResponse = {
            status: data.status === "ok" ? "healthy" : "unhealthy",
            version: data.version || "1.0.0",
            uptimeSeconds: data.uptimeSeconds || 0,
            components: componentsList
          };

          setHealth(adaptedData);
          setError(null);
          setLastCheckedAt(new Date());
          currentInterval = initialIntervalMs; // Reset backoff on success
        }
      } catch (err: any) {
        if (isMounted) {
          setError(err.message || "Failed to fetch health status.");
          setHealth(null);
          // Exponential backoff up to 60s
          currentInterval = Math.min(currentInterval * 1.5, 60000);
        }
      }

      if (isMounted) {
        timeoutId = setTimeout(checkHealth, currentInterval);
      }
    };

    // Start polling
    checkHealth();

    // Listen for visibility changes to resume polling immediately if tab becomes visible
    const handleVisibilityChange = () => {
      if (!document.hidden && isMounted) {
        clearTimeout(timeoutId);
        checkHealth();
      }
    };
    document.addEventListener("visibilitychange", handleVisibilityChange);

    return () => {
      isMounted = false;
      clearTimeout(timeoutId);
      document.removeEventListener("visibilitychange", handleVisibilityChange);
    };
  }, [initialIntervalMs]);

  return { health, error, lastCheckedAt };
}
