"use client";

import React from "react";
import { ChatMessage, Citation } from "../../lib/types/models";
import { cn } from "../../lib/utils";
import { CitationList } from "./CitationList";
import { PipelineVisualization } from "./PipelineVisualization";
import { MessageActions } from "./MessageActions";
import { Hexagon, User as UserIcon } from "lucide-react";

export function MessageBubble({ 
  message, 
  citations,
  onRegenerate
}: { 
  message: ChatMessage; 
  citations?: Citation[];
  onRegenerate?: () => void;
}) {
  const isUser = message.role === "user";

  const formatTime = (ts?: string) => {
    if (!ts) return "Just now";
    return new Intl.DateTimeFormat('en-US', { hour: 'numeric', minute: '2-digit' }).format(new Date(ts));
  };

  if (isUser) {
    return (
      <div className="flex w-full justify-end mb-6">
        <div className="flex flex-col max-w-[80%]">
          {/* User Bubble */}
          <div className="bg-[#1e2329] border border-[#30363d] rounded-2xl rounded-tr-sm px-5 py-4 text-sm leading-relaxed text-foreground shadow-sm animate-fade-in">
            <div className="whitespace-pre-wrap font-sans">{message.content}</div>
          </div>
          {/* Avatar & Timestamp below, right aligned (or could be above) */}
          <div className="flex items-center justify-end mt-2 space-x-2 text-xs text-muted-foreground">
            <span>{formatTime(message.timestamp)}</span>
            <div className="h-6 w-6 rounded-full overflow-hidden flex-shrink-0 border border-[#30363d]">
              <img src="https://i.pravatar.cc/150?u=admin" alt="Admin" className="h-full w-full object-cover" />
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex w-full justify-start mb-6 animate-fade-in">
      <div className="flex items-start max-w-full">
        {/* Assistant Avatar */}
        <div className="flex items-center justify-center relative w-8 h-8 mr-4 mt-1 flex-shrink-0">
          <Hexagon className="w-8 h-8 text-[#10b981] absolute fill-[#10b981]/10" />
          <span className="text-[10px] font-bold text-[#10b981] relative z-10">AI</span>
        </div>

        {/* Assistant Content */}
        <div className="flex flex-col flex-1 min-w-0">
          <div className="text-sm leading-relaxed text-foreground/90 font-sans">
            <div className="whitespace-pre-wrap">{message.content}</div>
          </div>
          
          <PipelineVisualization metadata={message.metadata as any} />
          {citations && citations.length > 0 && <CitationList citations={citations} />}

          {onRegenerate && (
            <MessageActions message={message} onRegenerate={onRegenerate} />
          )}
        </div>
      </div>
    </div>
  );
}
