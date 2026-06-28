"use client";

import React from "react";
import { useHealthPolling } from "../../lib/hooks/useHealthPolling";
import { HealthStatusCard } from "../../components/dashboard/HealthStatusCard";
import { ComponentHealthGrid } from "../../components/dashboard/ComponentHealthGrid";
import { MetricsPanel } from "../../components/dashboard/MetricsPanel";
import { Spinner } from "../../components/ui/Spinner";

export default function DashboardPage() {
  const { health, error, lastCheckedAt } = useHealthPolling(10000);

  return (
    <div className="container mx-auto p-4 md:p-6 lg:p-8 space-y-8">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b pb-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">System Health</h1>
          <p className="text-muted-foreground mt-2">
            Real-time observability of the RAG backend, Vector Store, and Cache components.
          </p>
        </div>
        <div className="flex flex-col items-end text-sm text-muted-foreground">
          {error ? (
            <span className="text-destructive font-medium">Polling Failed</span>
          ) : (
            <span className="flex items-center gap-2">
              <span className="relative flex h-2.5 w-2.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-green-500"></span>
              </span>
              Polling every 10s
            </span>
          )}
          {lastCheckedAt && <span>Last checked: {lastCheckedAt.toLocaleTimeString()}</span>}
        </div>
      </div>

      {!health && !error ? (
        <div className="flex h-64 items-center justify-center">
          <Spinner size="lg" className="text-muted-foreground" />
        </div>
      ) : error && !health ? (
        <div className="rounded-xl border border-destructive bg-destructive/10 p-6 text-destructive text-center">
          <h3 className="text-lg font-semibold mb-2">Backend Unreachable</h3>
          <p>{error}</p>
        </div>
      ) : (
        <div className="space-y-6">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <div className="md:col-span-2 lg:col-span-1">
              <HealthStatusCard status={health!.status} label="Overall System Status" />
            </div>
            <div className="md:col-span-2 lg:col-span-3">
              <MetricsPanel health={health} />
            </div>
          </div>
          
          <div>
            <h3 className="text-xl font-semibold mb-4 tracking-tight">Components</h3>
            <ComponentHealthGrid components={health!.components} />
          </div>
        </div>
      )}
    </div>
  );
}
