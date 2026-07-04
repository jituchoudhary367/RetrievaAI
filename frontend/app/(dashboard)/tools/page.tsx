"use client";

import React, { useState, useEffect, useCallback } from 'react';
import { TopBar } from '@/components/layout/TopBar';
import { ToolsStatsRow } from '@/components/tools/ToolsStatsRow';
import { ToolListArea } from '@/components/tools/ToolListArea';
import { ToolsRightPanel } from '@/components/tools/ToolsRightPanel';
import RequireAuth from '@/components/auth/RequireAuth';
import { toolsApi } from '@/lib/api/tools';
import { ToolRow, ToolExecutionRow } from '@/lib/types/backend';

export default function ToolsPage() {
  const [tools, setTools] = useState<ToolRow[]>([]);
  const [executions, setExecutions] = useState<Record<string, ToolExecutionRow[]>>({});
  const [recentExecutions, setRecentExecutions] = useState<ToolExecutionRow[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const fetchData = useCallback(async () => {
    try {
      const toolList = await toolsApi.listTools();
      setTools(toolList);

      // Fetch last 20 executions per tool in parallel
      const execMap: Record<string, ToolExecutionRow[]> = {};
      const allExecs: ToolExecutionRow[] = [];
      await Promise.allSettled(
        toolList.map(async t => {
          try {
            const execs = await toolsApi.getToolExecutions(t.id, 20);
            execMap[t.id] = execs;
            allExecs.push(...execs);
          } catch {
            execMap[t.id] = [];
          }
        })
      );
      setExecutions(execMap);
      // Sort all executions by date descending for recent executions panel
      allExecs.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());
      setRecentExecutions(allExecs.slice(0, 5));
    } catch (err) {
      console.error('Failed to load tools:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Compute aggregated stats from real data
  const activeTools = tools.filter(t => t.status === 'active').length;
  const allExecs = Object.values(executions).flat();
  const totalExecutions = allExecs.length;
  const successCount = allExecs.filter(e => e.status === 'success').length;
  const successRate = totalExecutions > 0 ? (successCount / totalExecutions) * 100 : 0;

  return (
    <RequireAuth>
      <div className="flex flex-col h-full bg-background relative overflow-hidden">
        <TopBar title="Tools" />
        <div className="flex flex-1 overflow-hidden">
          <div className="flex-1 flex flex-col min-w-0 border-r border-border bg-background p-4 overflow-y-auto space-y-4">
            <ToolsStatsRow
              totalTools={tools.length}
              activeTools={activeTools}
              totalExecutions={totalExecutions}
              successRate={successRate}
            />
            {isLoading ? (
              <div className="flex-1 flex items-center justify-center text-muted-foreground text-sm">
                Loading tools...
              </div>
            ) : (
              <ToolListArea tools={tools} executions={executions} />
            )}
          </div>
          <div className="w-80 flex-shrink-0 flex flex-col bg-muted/10 overflow-y-auto hidden lg:flex">
            <ToolsRightPanel
              tools={tools}
              recentExecutions={recentExecutions}
              showRegisterModal={() => {/* TODO: open register modal */}}
            />
          </div>
        </div>
      </div>
    </RequireAuth>
  );
}
