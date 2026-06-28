import { useState, useEffect } from "react";
import { HealthResponse } from "../types/models";
import { getHealth } from "../api/health";

export function useHealthPolling(intervalMs: number = 10000) {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [lastCheckedAt, setLastCheckedAt] = useState<Date | null>(null);

  useEffect(() => {
    let timeoutId: ReturnType<typeof setTimeout>;
    let isMounted = true;

    const checkHealth = async () => {
      try {
        const data = await getHealth();
        if (isMounted) {
          setHealth(data);
          setError(null);
          setLastCheckedAt(new Date());
        }
      } catch (err: any) {
        if (isMounted) {
          setError(err.message || "Failed to fetch health status.");
          setHealth(null);
        }
      }

      if (isMounted) {
        timeoutId = setTimeout(checkHealth, intervalMs);
      }
    };

    checkHealth();

    return () => {
      isMounted = false;
      clearTimeout(timeoutId);
    };
  }, [intervalMs]);

  return { health, error, lastCheckedAt };
}
