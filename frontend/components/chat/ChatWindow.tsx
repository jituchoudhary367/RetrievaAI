"use client";

import React, { useEffect, useRef } from "react";
import { ChatMessage, Citation } from "../../lib/types/models";
import { MessageBubble } from "./MessageBubble";
import { ChatInput } from "./ChatInput";
import { StreamingIndicator } from "./StreamingIndicator";
import { SuggestedFollowUps } from "./SuggestedFollowUps";
import { getRoles } from "../../lib/auth/session";

interface ChatWindowProps {
  messages: ChatMessage[];
  isStreaming: boolean;
  error: string | null;
  citations: Citation[];
  onSendMessage: (text: string) => void;
  onRegenerate: () => void;
}

export function ChatWindow({ 
  messages, 
  isStreaming, 
  error, 
  citations, 
  onSendMessage,
  onRegenerate
}: ChatWindowProps) {
  const bottomRef = useRef<HTMLDivElement>(null);
  
  // RBAC checks for UI presentation (backend still enforces strictly)
  const roles = getRoles();
  const canChat = roles.includes("member") || roles.includes("admin") || roles.includes("platform_admin");

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isStreaming]);

  return (
    <div className="flex flex-col h-full bg-transparent">
      <div className="flex-1 overflow-y-auto p-4 md:p-6 lg:p-8 scrollbar-thin">
        <div className="mx-auto flex max-w-3xl flex-col gap-6 pb-6">
          {messages.length === 0 ? (
            <div className="flex h-[50vh] flex-col items-center justify-center text-center animate-slide-up bg-[#161b22] border border-[#30363d] rounded-xl p-8 shadow-sm">
              <h2 className="mb-2 text-2xl font-bold tracking-tight text-foreground">
                How can I help you today?
              </h2>
              <p className="text-muted-foreground">
                Ask a question to search through your documents.
              </p>
            </div>
          ) : (
            messages.map((msg, i) => {
              const isLastAssistant = msg.role === "assistant" && i === messages.length - 1;
              return (
                <div key={i} className="flex flex-col gap-2">
                  <MessageBubble 
                    message={msg} 
                    citations={isLastAssistant ? citations : undefined} 
                    onRegenerate={isLastAssistant && !isStreaming ? onRegenerate : undefined}
                  />
                  {isLastAssistant && isStreaming && <StreamingIndicator />}
                  {isLastAssistant && !isStreaming && (
                    <SuggestedFollowUps onPick={(q) => onSendMessage(q)} />
                  )}
                </div>
              );
            })
          )}
          {error && (
            <div className="rounded-md bg-destructive/10 p-4 text-sm text-destructive">
              <strong>Error: </strong> {error}
            </div>
          )}
          <div ref={bottomRef} />
        </div>
      </div>
      <div className="mx-auto w-full max-w-3xl pb-4 px-4 md:px-0 bg-transparent">
        {canChat ? (
          <ChatInput onSend={onSendMessage} disabled={isStreaming} />
        ) : (
          <div className="flex h-12 w-full items-center justify-center rounded-xl border border-[#30363d] bg-[#161b22] px-4 text-sm text-muted-foreground shadow-sm opacity-60 cursor-not-allowed">
            Your role does not have permission to run queries.
          </div>
        )}
      </div>
    </div>
  );
}
