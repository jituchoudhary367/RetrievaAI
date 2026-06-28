"use client";

import React, { useEffect, useRef } from "react";
import { useChat } from "../../lib/hooks/useChat";
import { MessageBubble } from "./MessageBubble";
import { ChatInput } from "./ChatInput";
import { StreamingIndicator } from "./StreamingIndicator";

export function ChatWindow() {
  const { messages, sendMessage, isStreaming, error, citations } = useChat();
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="flex flex-col h-full bg-background">
      <div className="flex-1 overflow-y-auto p-4 md:p-6 lg:p-8">
        <div className="mx-auto flex max-w-3xl flex-col gap-6 pb-6">
          {messages.length === 0 ? (
            <div className="flex h-[50vh] flex-col items-center justify-center text-center">
              <h2 className="mb-2 text-2xl font-semibold tracking-tight text-foreground">
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
                  />
                  {isLastAssistant && isStreaming && <StreamingIndicator />}
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
      <div className="mx-auto w-full max-w-3xl border-t bg-background">
        <ChatInput onSend={(text) => sendMessage(text)} disabled={isStreaming} />
      </div>
    </div>
  );
}
