"use client";

import React from 'react';

const SUGGESTIONS = [
  "How does hybrid search work?",
  "What is CRAG?",
  "How is reranking done?",
  "Show me chunking strategies"
];

export function SuggestedFollowUps({ onPick }: { onPick: (q: string) => void }) {
  return (
    <div className="flex flex-col space-y-3 mt-6">
      <div className="text-xs text-muted-foreground">
        You can ask about:
      </div>
      <div className="flex flex-wrap gap-2">
        {SUGGESTIONS.map((q, i) => (
          <button
            key={i}
            onClick={() => onPick(q)}
            className="text-xs text-[#38bdf8] bg-[#0c1a25] hover:bg-[#112435] transition-colors border border-[#162e40] rounded-full px-4 py-2"
          >
            {q}
          </button>
        ))}
      </div>
    </div>
  );
}
