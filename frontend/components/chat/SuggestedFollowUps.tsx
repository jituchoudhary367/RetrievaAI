"use client";

import React, { useEffect, useState } from 'react';
import { getSuggestedQuestions } from '@/lib/api/query';

const DEFAULT_SUGGESTIONS = [
  "How does hybrid search work?",
  "What is CRAG?",
  "How is reranking done?",
  "Show me chunking strategies"
];

export function SuggestedFollowUps({ onPick }: { onPick: (q: string) => void }) {
  const [suggestions, setSuggestions] = React.useState<string[]>(DEFAULT_SUGGESTIONS);

  React.useEffect(() => {
    import('@/lib/api/query').then(({ getSuggestedQuestions }) => {
      getSuggestedQuestions()
        .then((data) => {
          if (data && data.length > 0) {
            setSuggestions(data);
          }
        })
        .catch((err) => {
          console.error("Failed to load dynamic suggestions:", err);
        });
    });
  }, []);

  return (
    <div className="flex flex-col space-y-3 mt-6">
      <div className="text-xs text-muted-foreground">
        You can ask about:
      </div>
      <div className="flex flex-wrap gap-2">
        {suggestions.map((q, i) => (
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
