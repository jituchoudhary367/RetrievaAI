import React from "react";
import { HealthStatus } from "../../lib/types/models";
import { Card, CardContent } from "../ui/card";
import { Badge } from "../ui/badge";
import { Activity, AlertTriangle, CheckCircle2 } from "lucide-react";

export function HealthStatusCard({ status, label }: { status: HealthStatus; label: string }) {
  const isHealthy = status === "healthy";
  const isDegraded = status === "degraded";

  const Icon = isHealthy ? CheckCircle2 : isDegraded ? Activity : AlertTriangle;
  const tone = isHealthy ? "success" : isDegraded ? "warning" : "destructive";

  return (
    <Card>
      <CardContent className="p-6 flex items-center justify-between">
        <div className="space-y-1">
          <p className="text-sm font-medium text-muted-foreground">{label}</p>
          <div className="flex items-center gap-2">
            <Icon className={`h-5 w-5 ${
              isHealthy ? "text-green-500" : isDegraded ? "text-yellow-500" : "text-red-500"
            }`} />
            <span className="text-2xl font-bold tracking-tight capitalize">
              {status}
            </span>
          </div>
        </div>
        <Badge tone={tone} className="uppercase text-[10px] tracking-wider">
          {status}
        </Badge>
      </CardContent>
    </Card>
  );
}
