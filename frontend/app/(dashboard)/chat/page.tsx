"use client";

import React, { useState, useEffect, useContext } from 'react';
import { TopBar } from '@/components/layout/TopBar';
import { ChatWindow } from '@/components/chat/ChatWindow';
import { SourcesPanel } from '@/components/sources/SourcesPanel';
import { ConversationsContext } from '@/components/layout/AppLayout';
import { useChat } from '@/lib/hooks/useChat';
import RequireAuth from '@/components/auth/RequireAuth';
import { ingestionApi } from '@/lib/api/ingest';

export default function ChatPage() {
  const [contextEnabled, setContextEnabled] = useState(true);
  
  // Get global conversation state
  const convContext = useContext(ConversationsContext);
  if (!convContext) {
    throw new Error("ChatPage must be rendered within AppLayout");
  }
  const { activeConversation, clearActive, updateActiveConversation } = convContext;

  // Local chat state
  const { messages, setMessages, sendMessage, isStreaming, error, citations, metadata } = useChat();

  // Sync activeConversation to local chat state on change
  useEffect(() => {
    if (activeConversation) {
      setMessages(activeConversation.messages);
      // We don't restore citations into the local useChat state because useChat's citations
      // only reflect the *latest* turn. We just set messages. 
    } else {
      setMessages([]);
    }
  }, [activeConversation?.sessionId, setMessages]); // only trigger on session change

  const handleSendMessage = async (text: string, useWebSearch: boolean = false) => {
    // Determine session ID
    let currentSessionId = activeConversation?.sessionId;
    if (!currentSessionId) {
      currentSessionId = crypto.randomUUID();
    }
    
    // We don't wait for sendMessage to finish here, it streams.
    // The useChat hook updates local messages. 
    await sendMessage(text, currentSessionId, useWebSearch);
  };

  const handleUpload = async (file: File) => {
    try {
      await ingestionApi.submitJob(file);
      // Optionally notify user of successful upload via a temporary system message
      // or simply rely on the background worker picking it up.
    } catch (error) {
      console.error("Failed to upload file:", error);
      alert("Failed to upload file: " + error);
    }
  };

  // Sync back to indexedDB when messages change significantly (i.e. at end of stream or user message)
  // Actually, useChat will update messages. We want to save to DB when stream ends.
  // We can just use an effect that watches `messages` and `isStreaming`
  useEffect(() => {
    if (!isStreaming && messages.length > 0) {
      const currentSessionId = activeConversation?.sessionId || messages[0].metadata?.sessionId || 'default';
      // It's a bit hacky to pull sessionId if it was newly generated. 
      // A better way is to ensure `updateActiveConversation` gets called.
      // We will pass down sessionId if activeConversation exists, but on first message we don't have it here.
      // So let's rely on updateActiveConversation finding or using a UUID.
      if (activeConversation) {
        updateActiveConversation(activeConversation.sessionId, messages, citations);
      } else {
        // First message of a new chat
        const newSessionId = crypto.randomUUID();
        updateActiveConversation(newSessionId, messages, citations);
      }
    }
  }, [isStreaming, messages.length]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleClearConversation = () => {
    clearActive();
  };

  return (
    <RequireAuth>
      <div className="flex flex-col h-full bg-background relative overflow-hidden">
        {/* Top Bar */}
        <TopBar 
          title={activeConversation?.title || "New Conversation"} 
          metadata={metadata} 
          editable
        />

        {/* Main Layout Area */}
        <div className="flex flex-1 overflow-hidden">
          
          {/* Center: Chat Window */}
          <div className="flex-1 flex flex-col min-w-0 border-r border-border bg-background relative z-10">
            <ChatWindow 
              messages={messages}
              isStreaming={isStreaming}
              error={error}
              citations={citations}
              onSendMessage={handleSendMessage}
              onUpload={handleUpload}
              onRegenerate={() => {
                if (messages.length >= 2) {
                  // Find last user message
                  const lastUserMsg = [...messages].reverse().find(m => m.role === 'user');
                  if (lastUserMsg) {
                    // The sendMessage in useChat currently just adds a new user message.
                    // We should ideally replace the last assistant message.
                    // For now, to keep it simple and within instructions, we just call sendMessage with same text.
                    handleSendMessage(lastUserMsg.content);
                  }
                }
              }}
            />
          </div>



        </div>
      </div>
    </RequireAuth>
  );
}
