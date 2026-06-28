import React from "react";
import { ChatMessage, Citation } from "../../lib/types/models";
import { cn } from "../../lib/utils";
import { CitationList } from "./CitationList";

export function MessageBubble({ message, citations }: { message: ChatMessage; citations?: Citation[] }) {
  const isUser = message.role === "user";

  return (
    <div
      className={cn(
        "flex w-full",
        isUser ? "justify-end" : "justify-start"
      )}
    >
      <div
        className={cn(
          "max-w-[85%] rounded-2xl px-5 py-3.5 text-[15px] leading-relaxed shadow-sm",
          isUser
            ? "bg-primary text-primary-foreground rounded-tr-sm"
            : "bg-card text-card-foreground border rounded-tl-sm"
        )}
      >
        <div className="whitespace-pre-wrap font-sans">{message.content}</div>
        {!isUser && citations && <CitationList citations={citations} />}
      </div>
    </div>
  );
}
