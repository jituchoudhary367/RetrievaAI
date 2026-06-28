import React, { useState } from "react";
import { SendHorizontal, Paperclip, Globe, SlidersHorizontal } from "lucide-react";

export function ChatInput({ onSend, disabled }: { onSend: (text: string) => void; disabled?: boolean }) {
  const [value, setValue] = useState("");
  const [webSearch, setWebSearch] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (value.trim() && !disabled) {
      onSend(value.trim());
      setValue("");
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e as unknown as React.FormEvent);
    }
  };

  return (
    <div className="w-full flex flex-col items-center">
      <form 
        onSubmit={handleSubmit} 
        className="relative flex flex-col w-full p-4 bg-[#161b22] border border-[#30363d] rounded-xl shadow-lg"
      >
        <textarea
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask anything about your documents..."
          disabled={disabled}
          className="w-full min-h-[44px] max-h-48 resize-none bg-transparent border-none focus:outline-none text-sm text-foreground placeholder-muted-foreground mb-4"
          rows={1}
        />
        
        <div className="flex items-center justify-between mt-auto">
          {/* Left Actions */}
          <div className="flex items-center space-x-2">
            <button 
              type="button"
              disabled
              className="flex items-center justify-center p-2 rounded-md border border-[#30363d] bg-[#0d1117] text-muted-foreground hover:text-foreground transition-colors opacity-60 cursor-not-allowed"
              title="Attach (coming soon)"
            >
              <Paperclip className="h-4 w-4" />
            </button>
            <button 
              type="button"
              disabled
              className="flex items-center justify-center px-3 py-2 space-x-2 rounded-md border border-[#30363d] bg-[#0d1117] text-muted-foreground hover:text-foreground transition-colors opacity-60 cursor-not-allowed"
              title="Filters (coming soon)"
            >
              <SlidersHorizontal className="h-4 w-4" />
              <span className="text-xs font-medium">Filters</span>
            </button>
            <button 
              type="button"
              onClick={() => setWebSearch(!webSearch)}
              className={`flex items-center justify-center px-3 py-2 space-x-2 rounded-md border ${webSearch ? 'border-[#10b981]/50 bg-[#122822]' : 'border-[#30363d] bg-[#0d1117]'} text-muted-foreground transition-colors`}
              title="Toggle Web Search"
            >
              <Globe className={`h-4 w-4 ${webSearch ? 'text-[#10b981]' : ''}`} />
              <span className={`text-xs font-medium ${webSearch ? 'text-[#10b981]' : ''}`}>Web Search</span>
              {/* Toggle switch visual */}
              <div className={`ml-2 w-7 h-4 rounded-full flex items-center p-0.5 transition-colors ${webSearch ? 'bg-[#10b981]' : 'bg-[#30363d]'}`}>
                <div className={`w-3 h-3 rounded-full bg-white transition-transform ${webSearch ? 'translate-x-3' : 'translate-x-0'}`} />
              </div>
            </button>
          </div>

          {/* Right Action */}
          <button
            type="submit"
            disabled={disabled || !value.trim()}
            className="flex items-center justify-center p-2 rounded-md bg-[#10b981] hover:bg-[#059669] text-white disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            title="Send Message"
          >
            <SendHorizontal className="h-5 w-5" />
          </button>
        </div>
      </form>
      <div className="w-full mt-3 flex items-center text-[10px] text-muted-foreground/60 space-x-1 justify-start px-2">
        <span>Press Enter to send</span>
        <span>•</span>
        <span>Shift + Enter for new line</span>
      </div>
    </div>
  );
}
