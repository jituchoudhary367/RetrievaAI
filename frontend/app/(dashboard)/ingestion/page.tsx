"use client";

import React, { useState, useEffect, useCallback } from 'react';
import { TopBar } from '@/components/layout/TopBar';
import { IngestionStatsRow } from '@/components/ingestion/IngestionStatsRow';
import { IngestionUploadArea } from '@/components/ingestion/IngestionUploadArea';
import { IngestionListArea } from '@/components/ingestion/IngestionListArea';
import { IngestionDetailPanel } from '@/components/ingestion/IngestionDetailPanel';
import RequireAuth from '@/components/auth/RequireAuth';
import { ingestionApi } from '@/lib/api/ingest';

export default function IngestionPage() {
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);
  const [jobs, setJobs] = useState<any[]>([]);
  const [rawJobs, setRawJobs] = useState<any[]>([]);

  const fetchJobs = useCallback(async () => {
    try {
      const res = await ingestionApi.listJobs();
      const items = res.items || res || [];
      setRawJobs(items);
      const mapped = items.map((job: any) => ({
        id: job.id,
        type: (job.source_path_or_url || '').split('.').pop()?.toLowerCase() || 'unknown',
        title: (job.source_path_or_url || '').split('/').pop() || job.source_path_or_url || 'Untitled',
        subtitle: `ID: ${(job.id || '').substring(0, 8)}`,
        source: job.source_path_or_url,
        status: job.status,
        progress: job.progress_percent,
        chunks: job.chunks_total,
        indexed: job.chunks_indexed,
        started: job.started_at ? new Date(job.started_at).toLocaleString() : 'N/A',
        durationMs: job.completed_at && job.started_at
          ? new Date(job.completed_at).getTime() - new Date(job.started_at).getTime()
          : undefined,
      }));
      setJobs(mapped);
    } catch (err) {
      console.error('Failed to load ingestion jobs:', err);
    }
  }, []);

  // Poll every 5s unconditionally for real-time updates
  useEffect(() => {
    fetchJobs();
    const interval = setInterval(fetchJobs, 5000);
    return () => clearInterval(interval);
  }, [fetchJobs]);

  // Compute stats from real jobs
  const totalJobs = rawJobs.length;
  const totalChunks = rawJobs.reduce((sum, j) => sum + (j.chunks_total || 0), 0);
  const completedJobs = rawJobs.filter(j => j.status === 'completed');
  const failedJobs = rawJobs.filter(j => j.status === 'failed');
  const terminalJobs = completedJobs.length + failedJobs.length;
  const successRate = terminalJobs > 0 ? (completedJobs.length / terminalJobs) * 100 : 0;
  const durations = rawJobs
    .filter(j => j.completed_at && j.started_at)
    .map(j => new Date(j.completed_at).getTime() - new Date(j.started_at).getTime());
  const avgProcessingMs = durations.length > 0
    ? durations.reduce((a, b) => a + b, 0) / durations.length
    : undefined;

  const selectedJob = jobs.find(j => j.id === selectedJobId);

  return (
    <RequireAuth>
      <div className="flex flex-col h-full bg-background relative overflow-hidden">
        <TopBar title="Ingestion" />
        <div className="flex flex-1 overflow-hidden">
          <div className="flex-1 flex flex-col min-w-0 border-r border-border bg-background p-4 overflow-y-auto space-y-4">
            <IngestionStatsRow
              totalJobs={totalJobs}
              totalChunks={totalChunks}
              successRate={successRate}
              avgProcessingMs={avgProcessingMs}
            />
            <div className="grid grid-cols-1 gap-4">
              <IngestionUploadArea onUploadSuccess={fetchJobs} />
            </div>
            <IngestionListArea jobs={jobs} selectedJobId={selectedJobId} onSelectJob={setSelectedJobId} />
          </div>
          {selectedJob && (
            <div className="w-80 flex-shrink-0 flex flex-col border-l border-border bg-muted/10 overflow-y-auto hidden lg:flex">
              <div className="flex-1 p-2 space-y-2">
                <IngestionDetailPanel 
                  job={selectedJob} 
                  onClose={async (id?: string, shouldDelete?: boolean) => {
                    if (shouldDelete && id) {
                      try {
                        await ingestionApi.deleteJob(id);
                        await fetchJobs();
                      } catch(e) {
                        console.error(e);
                        alert("Failed to delete job.");
                      }
                    }
                    setSelectedJobId(null);
                  }} 
                />
              </div>
            </div>
          )}
        </div>
      </div>
    </RequireAuth>
  );
}
