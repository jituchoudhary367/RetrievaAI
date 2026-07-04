"use client";

import React from "react";
import { ChatMessage, Citation } from "../../lib/types/models";
import { cn } from "../../lib/utils";
import { CitationList } from "./CitationList";
import { MessageActions } from "./MessageActions";
import { Hexagon, User as UserIcon } from "lucide-react";
import { getUserInfo } from "../../lib/auth/session";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

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
  
  const userInfo = isUser ? getUserInfo() : null;
  const avatarUrl = userInfo?.avatarUrl || "https://i.pravatar.cc/150?u=admin";

  if (isUser) {
    return (
      <div className="flex w-full justify-end animate-fade-in group mt-4">
        <div className="flex items-start max-w-[85%] justify-end">
          <div className="flex flex-col items-end min-w-0">
            {/* User Bubble */}
            <div className="bg-[#2b313a] border border-[#3a414b] rounded-2xl rounded-tr-sm px-4 py-3 text-[15px] leading-relaxed text-foreground shadow-sm overflow-x-auto">
              <div className="whitespace-pre-wrap font-sans break-words">{message.content}</div>
            </div>
            {/* Timestamp hidden until hover */}
            <span className="text-[10px] text-muted-foreground mt-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
              {formatTime(message.timestamp)}
            </span>
          </div>
          {/* User Avatar */}
          <div className="flex items-center justify-center relative w-8 h-8 ml-3 flex-shrink-0 rounded-full overflow-hidden border border-[#30363d]">
            <img src={avatarUrl} alt="User" className="h-full w-full object-cover" />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex w-full justify-start animate-fade-in mt-6 mb-2">
      <div className="flex items-start max-w-[90%]">
        {/* Assistant Avatar */}
        <div className="flex items-center justify-center relative w-8 h-8 mr-4 mt-0.5 flex-shrink-0">
          <Hexagon className="w-8 h-8 text-[#10b981] absolute fill-[#10b981]/10" />
          <span className="text-[10px] font-bold text-[#10b981] relative z-10">AI</span>
        </div>

        {/* Assistant Content */}
        <div className="flex flex-col flex-1 min-w-0">
          <div className="text-[15px] leading-relaxed text-foreground/90 font-sans break-words overflow-x-auto prose prose-invert prose-sm max-w-none">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {message.content}
            </ReactMarkdown>
          </div>
          {citations && citations.length > 0 && <div className="mt-4"><CitationList citations={citations} /></div>}

          {onRegenerate && (
            <div className="mt-2">
              <MessageActions message={message} onRegenerate={onRegenerate} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
