import React from "react";
import { SearchResult } from "../../lib/types/models";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/Card";
import { Badge } from "../ui/Badge";

export function ResultCard({ result }: { result: SearchResult }) {
  const isVector = result.source === "vector";
  
  return (
    <Card className="overflow-hidden">
      <CardHeader className="bg-muted/30 p-4 py-3 border-b">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-semibold truncate pr-4">
            {result.documentId}
          </CardTitle>
          <div className="flex items-center gap-2 flex-shrink-0">
            <Badge tone={isVector ? "default" : "neutral"} className="text-[10px] px-1.5 py-0">
              {result.source.toUpperCase()}
            </Badge>
            <span className="text-xs font-mono text-muted-foreground">
              {result.score.toFixed(3)}
            </span>
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-4">
        <p className="text-sm text-foreground/90 whitespace-pre-wrap leading-relaxed">
          {result.text}
        </p>
        {result.metadata && Object.keys(result.metadata).length > 0 && (
          <div className="mt-3 pt-3 border-t flex flex-wrap gap-1.5">
            {Object.entries(result.metadata).map(([k, v]) => (
              <span key={k} className="inline-flex items-center rounded border px-1.5 py-0.5 text-[10px] font-medium text-muted-foreground bg-muted/20">
                {k}: {String(v)}
              </span>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
