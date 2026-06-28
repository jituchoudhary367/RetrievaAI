"use client";

import React from 'react';
import { Hammer } from 'lucide-react';

export function PlaceholderPage({ title, description }: { title: string; description: string }) {
  return (
    <div className="flex-1 flex flex-col items-center justify-center h-full p-8 text-center bg-background">
      <div className="glass-panel p-12 rounded-xl flex flex-col items-center max-w-md animate-fade-in">
        <div className="h-16 w-16 bg-primary/10 rounded-full flex items-center justify-center mb-6">
          <Hammer className="h-8 w-8 text-primary" />
        </div>
        <h2 className="text-2xl font-bold tracking-tight mb-2">{title}</h2>
        <p className="text-muted-foreground">{description}</p>
        <div className="mt-8 px-4 py-2 bg-muted text-xs font-mono rounded text-muted-foreground border border-border/50">
          🚧 Under Construction
        </div>
      </div>
    </div>
  );
}
