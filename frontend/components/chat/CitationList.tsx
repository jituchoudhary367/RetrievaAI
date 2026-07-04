import React from "react";
import { Citation } from "../../lib/types/models";
import { Badge } from "../ui/badge";

export function CitationList({ citations }: { citations: Citation[] }) {
  if (!citations || citations.length === 0) return null;

  return (
    <div className="mt-3 flex flex-wrap gap-2 text-xs text-muted-foreground">
      {citations.map((citation) => (
        <a
          key={citation.citationId}
          href={citation.url || "#"}
          target={citation.url ? "_blank" : undefined}
          rel="noopener noreferrer"
          title={citation.textSnippet}
          className="group inline-flex items-center gap-1 hover:text-foreground transition-colors"
        >
          <Badge tone="neutral" className="px-1.5 py-0 group-hover:bg-primary/20 cursor-pointer">
            [{citation.citationId}]
          </Badge>
          <span className="truncate max-w-[150px]">{citation.documentId}</span>
        </a>
      ))}
    </div>
  );
}
