import React from "react";

export function StreamingIndicator() {
  return (
    <div className="flex items-center space-x-1.5 mt-2 ml-1">
      <div className="w-2 h-2 bg-foreground rounded-full animate-bounce [animation-delay:-0.3s]"></div>
      <div className="w-2 h-2 bg-foreground rounded-full animate-bounce [animation-delay:-0.15s]"></div>
      <div className="w-2 h-2 bg-foreground rounded-full animate-bounce"></div>
    </div>
  );
}
