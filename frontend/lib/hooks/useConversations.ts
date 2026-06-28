import { useState, useEffect, useCallback } from 'react';
import { 
  ConversationSummary, 
  StoredConversation, 
  listConversations, 
  getConversation, 
  saveConversation, 
  deleteConversation 
} from '../storage/conversationStore';
import { ChatMessage, Citation } from '../types/models';

export function useConversations() {
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [activeConversation, setActiveConversation] = useState<StoredConversation | null>(null);

  const loadList = useCallback(async () => {
    const list = await listConversations();
    setConversations(list);
  }, []);

  useEffect(() => {
    loadList();
  }, [loadList]);

  const selectConversation = useCallback(async (sessionId: string) => {
    const conv = await getConversation(sessionId);
    if (conv) {
      setActiveConversation(conv);
    }
  }, []);

  const startNew = useCallback(() => {
    setActiveConversation(null);
  }, []);

  const clearActive = useCallback(async () => {
    if (activeConversation) {
      await deleteConversation(activeConversation.sessionId);
      await loadList();
    }
    setActiveConversation(null);
  }, [activeConversation, loadList]);

  const updateActiveConversation = useCallback(async (
    sessionId: string, 
    messages: ChatMessage[], 
    citations: Citation[]
  ) => {
    if (messages.length === 0) return;
    
    const title = messages[0].content.substring(0, 40) + (messages[0].content.length > 40 ? '...' : '');
    const conv: StoredConversation = {
      sessionId,
      title,
      messages,
      citations,
      updatedAt: Date.now()
    };
    await saveConversation(conv);
    setActiveConversation(conv);
    await loadList();
  }, [loadList]);

  return {
    conversations,
    activeConversation,
    selectConversation,
    startNew,
    clearActive,
    updateActiveConversation
  };
}
