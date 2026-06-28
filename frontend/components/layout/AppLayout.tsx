"use client";

import React from 'react';
import { Sidebar } from './Sidebar';
import { useConversations } from '../../lib/hooks/useConversations';

export const ConversationsContext = React.createContext<ReturnType<typeof useConversations> | null>(null);

export function AppLayout({ children }: { children: React.ReactNode }) {
  const conversationsData = useConversations();

  return (
    <ConversationsContext.Provider value={conversationsData}>
      <div className="flex h-screen overflow-hidden bg-background">
        {/* Sidebar now contains the status bar */}
        <Sidebar conversationsContext={conversationsData} />
        
        {/* Main Content Area */}
        <div className="flex-1 flex flex-col min-w-0">
          {children}
        </div>
      </div>
    </ConversationsContext.Provider>
  );
}
