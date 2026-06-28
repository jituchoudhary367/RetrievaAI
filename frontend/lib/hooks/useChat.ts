import { useState, useCallback, useRef } from "react";
import { ChatMessage, Citation, StreamChunk, QueryRequest, StreamEventType } from "../types/models";
import { streamQuery } from "../api/query";

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [citations, setCitations] = useState<Citation[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const abortControllerRef = useRef<AbortController | null>(null);

  const sendMessage = useCallback(
    async (text: string, sessionId?: string) => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      abortControllerRef.current = new AbortController();

      const userMsg: ChatMessage = { role: "user", content: text };
      setMessages((prev) => [...prev, userMsg]);
      setError(null);
      setIsStreaming(true);

      const request: QueryRequest = {
        query: text,
        sessionId,
        stream: true,
      };

      let assistantResponse = "";

      const onChunk = (chunk: StreamChunk) => {
        switch (chunk.event as StreamEventType) {
          case "start":
            // Create a new assistant message slot
            setMessages((prev) => {
              const last = prev[prev.length - 1];
              if (last && last.role === "assistant") return prev;
              return [...prev, { role: "assistant", content: "" }];
            });
            break;
          case "token":
            if (chunk.delta) {
              assistantResponse += chunk.delta;
              setMessages((prev) => {
                const newMessages = [...prev];
                const lastIdx = newMessages.length - 1;
                if (newMessages[lastIdx].role === "assistant") {
                  newMessages[lastIdx].content = assistantResponse;
                }
                return newMessages;
              });
            }
            break;
          case "citation":
            if (chunk.citation) {
              setCitations((prev) => {
                // Avoid duplicates
                if (prev.some((c) => c.citationId === chunk.citation!.citationId)) return prev;
                return [...prev, chunk.citation!];
              });
            }
            break;
          case "error":
            if (chunk.errorMessage) {
              setError(chunk.errorMessage);
            }
            break;
          case "end":
            setIsStreaming(false);
            break;
          case "tool_call":
          case "tool_result":
            // Optional: Handle tool events in the UI if needed
            break;
        }
      };

      try {
        await streamQuery(request, onChunk, abortControllerRef.current.signal);
      } catch (err: any) {
        if (err.name !== "AbortError") {
          setError(err.message || "An unexpected error occurred.");
        }
      } finally {
        setIsStreaming(false);
      }
    },
    []
  );

  return { messages, sendMessage, isStreaming, error, citations };
}
