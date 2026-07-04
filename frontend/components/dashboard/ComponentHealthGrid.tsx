import React from "react";
import { ComponentHealth } from "../../lib/types/models";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";

export function ComponentHealthGrid({ components }: { components: ComponentHealth[] }) {
  if (!components || components.length === 0) return null;

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {components.map((comp) => (
        <Card key={comp.name} className="overflow-hidden">
          <CardHeader className="bg-muted/30 p-4 border-b">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-semibold truncate capitalize">
                {comp.name}
              </CardTitle>
              <Badge 
                tone={comp.status === "healthy" ? "success" : comp.status === "degraded" ? "warning" : "destructive"} 
                className="text-[10px] px-1.5 py-0"
              >
                {comp.status}
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="p-4 space-y-2 text-sm">
            {comp.latencyMs !== undefined && (
              <div className="flex justify-between">
                <span className="text-muted-foreground">Latency</span>
                <span className="font-mono font-medium">{comp.latencyMs.toFixed(1)} ms</span>
              </div>
            )}
            {comp.detail && (
              <div className="flex flex-col mt-2 pt-2 border-t text-xs text-muted-foreground">
                <span className="font-medium mb-1">Details:</span>
                <span className="break-all">{comp.detail}</span>
              </div>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
