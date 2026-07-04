import React, { useState, useRef } from "react";
import { SendHorizontal, Paperclip, Globe, SlidersHorizontal, File as FileIcon, X } from "lucide-react";

export function ChatInput({ onSend, onUpload, disabled }: { onSend: (text: string, useWebSearch: boolean) => void; onUpload?: (file: File) => void; disabled?: boolean }) {
  const [value, setValue] = useState("");
  const [webSearch, setWebSearch] = useState(false);
  const [attachedFile, setAttachedFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if ((value.trim() || attachedFile) && !disabled) {
      if (attachedFile && onUpload) {
        onUpload(attachedFile);
        setAttachedFile(null);
      }
      if (value.trim()) {
        onSend(value.trim(), webSearch);
      }
      setValue("");
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setAttachedFile(e.target.files[0]);
    }
  };

  const clearAttachment = () => {
    setAttachedFile(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
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
        className="relative flex flex-col w-full p-3 bg-[#161b22] border border-[#30363d] rounded-2xl shadow-sm focus-within:ring-1 focus-within:ring-[#10b981]/50 focus-within:border-[#10b981]/50 transition-all"
      >
        {attachedFile && (
          <div className="flex items-center gap-2 mb-3 bg-[#0d1117] border border-[#30363d] rounded-md px-3 py-1.5 w-max">
            <FileIcon className="h-4 w-4 text-muted-foreground" />
            <span className="text-xs text-foreground truncate max-w-[200px]">{attachedFile.name}</span>
            <button type="button" onClick={clearAttachment} className="text-muted-foreground hover:text-red-400 ml-1">
              <X className="h-3 w-3" />
            </button>
          </div>
        )}
        <textarea
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask anything about your documents..."
          disabled={disabled}
          className="w-full min-h-[44px] max-h-48 resize-none bg-transparent border-none focus:outline-none text-sm text-foreground placeholder-muted-foreground mb-2"
          rows={1}
        />
        
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          className="hidden"
          accept=".pdf,.txt,.docx,.md,.csv"
        />
        
        <div className="flex items-center justify-between mt-auto">
          {/* Left Actions */}
          <div className="flex items-center space-x-2">
            <button 
              type="button"
              disabled={disabled}
              onClick={() => fileInputRef.current?.click()}
              className="flex items-center justify-center p-2 rounded-md border border-[#30363d] bg-[#0d1117] text-muted-foreground hover:text-foreground transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              title="Attach File"
            >
              <Paperclip className="h-4 w-4" />
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
            disabled={disabled || (!value.trim() && !attachedFile)}
            className="flex items-center justify-center p-2 rounded-md bg-[#10b981] hover:bg-[#059669] text-white disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            title="Send Message"
          >
            <SendHorizontal className="h-5 w-5" />
          </button>
        </div>
      </form>
    </div>
  );
}
