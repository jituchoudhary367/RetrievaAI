import React from "react";
import { HealthResponse } from "../../lib/types/models";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/Card";
import { Activity, Clock } from "lucide-react";

export function MetricsPanel({ health }: { health: HealthResponse | null }) {
  if (!health) return null;

  const uptimeHours = (health.uptimeSeconds / 3600).toFixed(1);
  const uptimeDays = (health.uptimeSeconds / 86400).toFixed(1);

  return (
    <Card>
      <CardHeader className="bg-muted/30 p-4 border-b">
        <div className="flex items-center gap-2">
          <Activity className="h-4 w-4 text-muted-foreground" />
          <CardTitle className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">
            System Metrics
          </CardTitle>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <div className="grid grid-cols-2 divide-x divide-y md:grid-cols-4 md:divide-y-0">
          <div className="p-4 flex flex-col gap-1 text-center">
            <span className="text-xs font-medium text-muted-foreground">Version</span>
            <span className="text-lg font-mono font-semibold">{health.version}</span>
          </div>
          <div className="p-4 flex flex-col gap-1 text-center">
            <span className="text-xs font-medium text-muted-foreground">Uptime</span>
            <span className="text-lg font-mono font-semibold">
              {health.uptimeSeconds > 86400 ? `${uptimeDays} d` : `${uptimeHours} h`}
            </span>
          </div>
          <div className="p-4 flex flex-col gap-1 text-center">
            <span className="text-xs font-medium text-muted-foreground">Components</span>
            <span className="text-lg font-mono font-semibold">
              {health.components?.length || 0}
            </span>
          </div>
          <div className="p-4 flex flex-col gap-1 text-center items-center justify-center">
            <Clock className="h-5 w-5 text-muted-foreground opacity-50" />
            <span className="text-[10px] text-muted-foreground uppercase tracking-widest mt-1">
              Live
            </span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
