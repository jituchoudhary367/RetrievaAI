"use client";

import React from 'react';
import { ResponseMetadata } from '../../lib/types/models';
import { Trash2, ChevronDown } from 'lucide-react';

export function ConversationContextPanel({ 
  metadata, 
  contextEnabled, 
  onToggleContext, 
  onClear 
}: { 
  metadata?: ResponseMetadata; 
  contextEnabled: boolean;
  onToggleContext: () => void;
  onClear: () => void;
}) {
  const tokenUsage = metadata?.tokenUsage?.totalTokens || 0;
  const maxTokens = 16384;
  const percentage = Math.min((tokenUsage / maxTokens) * 100, 100);

  return (
    <div className="flex flex-col space-y-4 p-4">
      <h3 className="text-sm font-semibold text-foreground mb-1">Conversation Context</h3>
      
      <div className="space-y-4">
        {/* Window Size */}
        <div className="flex items-center justify-between text-xs">
          <span className="text-muted-foreground">Window Size</span>
          <div className="flex items-center space-x-2 bg-[#161b22] border border-[#30363d] px-2 py-1 rounded cursor-not-allowed">
            <span className="text-foreground">10 turns</span>
            <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" />
          </div>
        </div>

        {/* Token Usage */}
        <div className="flex flex-col space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span className="text-muted-foreground">Token Usage</span>
            <span className="text-muted-foreground font-medium">
              <span className="text-foreground">{tokenUsage.toLocaleString()}</span> / {maxTokens.toLocaleString()}
            </span>
          </div>
          {/* Progress bar */}
          <div className="h-1.5 w-full bg-[#161b22] rounded-full overflow-hidden border border-[#30363d]">
            <div 
              className="h-full bg-[#10b981] rounded-full" 
              style={{ width: `${Math.max(percentage, 5)}%` }} // Ensure a small sliver is visible if 0
            />
          </div>
        </div>

        {/* Clear Conversation */}
        <button 
          onClick={onClear}
          className="w-full flex items-center justify-center space-x-2 bg-transparent text-red-500 hover:bg-red-500/10 border border-red-500/30 px-3 py-2 rounded-md transition-colors text-xs font-medium mt-2"
        >
          <Trash2 className="h-3.5 w-3.5" />
          <span>Clear Conversation</span>
        </button>

      </div>
    </div>
  );
}
