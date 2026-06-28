"use client";

import React, { useState } from 'react';
import { ChatMessage } from '../../lib/types/models';
import { Copy, RefreshCw, Share2, ThumbsUp, ThumbsDown, Check } from 'lucide-react';

export function MessageActions({ 
  message, 
  onRegenerate 
}: { 
  message: ChatMessage; 
  onRegenerate: () => void;
}) {
  const [copiedText, setCopiedText] = useState(false);
  const [copiedShare, setCopiedShare] = useState(false);
  const [feedback, setFeedback] = useState<'up' | 'down' | null>(null);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message.content);
      setCopiedText(true);
      setTimeout(() => setCopiedText(false), 2000);
    } catch (err) {
      console.error("Failed to copy text", err);
    }
  };

  const handleShare = async () => {
    try {
      const shareText = `Q: [User Question]\nA: ${message.content}`;
      await navigator.clipboard.writeText(shareText);
      setCopiedShare(true);
      setTimeout(() => setCopiedShare(false), 2000);
    } catch (err) {
      console.error("Failed to copy share text", err);
    }
  };

  const handleFeedback = (type: 'up' | 'down') => {
    setFeedback(prev => prev === type ? null : type);
  };

  return (
    <div className="flex items-center justify-between mt-4 text-xs font-medium text-muted-foreground w-full">
      <div className="flex items-center space-x-4">
        <button 
          onClick={handleCopy}
          className="hover:text-foreground transition-colors flex items-center space-x-1.5"
        >
          {copiedText ? <Check className="h-3.5 w-3.5 text-green-500" /> : <Copy className="h-3.5 w-3.5" />}
          <span>Copy</span>
        </button>

        <button 
          onClick={onRegenerate}
          className="hover:text-foreground transition-colors flex items-center space-x-1.5"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          <span>Regenerate</span>
        </button>

        <button 
          onClick={handleShare}
          className="hover:text-foreground transition-colors flex items-center space-x-1.5"
        >
          {copiedShare ? <Check className="h-3.5 w-3.5 text-green-500" /> : <Share2 className="h-3.5 w-3.5" />}
          <span>Share</span>
        </button>
      </div>

      <div className="flex items-center space-x-3">
        <button 
          onClick={() => handleFeedback('up')}
          className={`transition-colors flex items-center justify-center ${
            feedback === 'up' ? 'text-[#10b981]' : 'hover:text-foreground'
          }`}
        >
          <ThumbsUp className="h-3.5 w-3.5" />
        </button>

        <button 
          onClick={() => handleFeedback('down')}
          className={`transition-colors flex items-center justify-center ${
            feedback === 'down' ? 'text-destructive' : 'hover:text-foreground'
          }`}
        >
          <ThumbsDown className="h-3.5 w-3.5" />
        </button>
      </div>
    </div>
  );
}
