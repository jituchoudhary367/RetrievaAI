import React, { useState, useRef, useEffect } from 'react';
import { ConversationSummary } from '../../lib/storage/conversationStore';
import { Search } from 'lucide-react';

export function ConversationList({ 
  conversations, 
  activeId, 
  onSelect 
}: { 
  conversations: ConversationSummary[]; 
  activeId: string | null; 
  onSelect: (id: string) => void;
}) {
  const [searchQuery, setSearchQuery] = useState("");
  const [showSearch, setShowSearch] = useState(false);
  const [visibleCount, setVisibleCount] = useState(10);
  const searchContainerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (showSearch && inputRef.current) {
      inputRef.current.focus();
    }
  }, [showSearch]);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (searchContainerRef.current && !searchContainerRef.current.contains(e.target as Node)) {
        setShowSearch(false);
        setSearchQuery("");
      }
    };
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setShowSearch(false);
        setSearchQuery("");
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleEscape);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleEscape);
    };
  }, []);

  const filteredConversations = conversations.filter(c => 
    (c.title || "New Conversation").toLowerCase().includes(searchQuery.toLowerCase())
  );

  const todayDate = new Date();
  todayDate.setHours(0,0,0,0);
  const today = todayDate.getTime();
  const sevenDaysAgo = today - 7 * 24 * 60 * 60 * 1000;
  
  const todayConvs = filteredConversations.filter(c => c.updatedAt >= today);
  const previousConvs = filteredConversations.filter(c => c.updatedAt >= sevenDaysAgo && c.updatedAt < today);
  const olderConvs = filteredConversations.filter(c => c.updatedAt < sevenDaysAgo);

  const formatTime = (ts: number) => {
    return new Intl.DateTimeFormat('en-US', { hour: '2-digit', minute: '2-digit' }).format(new Date(ts));
  };
  const formatDate = (ts: number) => {
    return new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric' }).format(new Date(ts));
  };

  let currentDisplayed = 0;

  const renderGroup = (title: string, list: ConversationSummary[], isToday: boolean) => {
    if (list.length === 0 || currentDisplayed >= visibleCount) return null;
    
    // Slice list so we don't exceed visibleCount globally
    const remainingSlots = visibleCount - currentDisplayed;
    const itemsToShow = list.slice(0, remainingSlots);
    currentDisplayed += itemsToShow.length;

    return (
      <div className="mb-4 px-2">
        <h4 className="px-2 text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-2">
          {title}
        </h4>
        <ul className="space-y-0.5">
          {itemsToShow.map(c => {
            const isActive = activeId === c.sessionId;
            return (
              <li key={c.sessionId}>
                <button
                  onClick={() => onSelect(c.sessionId)}
                  className={`w-full flex items-center justify-between text-left px-2 py-2 text-xs rounded-md transition-colors ${
                    isActive
                      ? 'bg-[#122822] text-[#e6edf3] font-medium' 
                      : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                  }`}
                >
                  <span className="truncate flex-1 pr-2">{c.title || "New Conversation"}</span>
                  <span className={`flex-shrink-0 text-[10px] ${isActive ? 'text-[#10b981]' : 'text-muted-foreground/60'}`}>
                    {isToday ? formatTime(c.updatedAt) : formatDate(c.updatedAt)}
                  </span>
                </button>
              </li>
            );
          })}
        </ul>
      </div>
    );
  };

  const hasMore = visibleCount < filteredConversations.length;

  return (
    <div className="flex-1 overflow-y-auto py-2 scrollbar-thin flex flex-col">
      <div className="px-4 py-2 flex flex-col mb-2 relative" ref={searchContainerRef}>
        <div className="flex items-center justify-between text-muted-foreground">
          <span className="text-[10px] font-bold tracking-widest uppercase">Conversations</span>
          <div className="flex space-x-2">
            <button 
              onClick={() => setShowSearch(true)}
              className="hover:text-foreground transition-colors focus:outline-none"
            >
              <Search className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>
        <div 
          className={`overflow-hidden transition-all duration-300 ease-in-out ${
            showSearch ? "max-h-12 opacity-100 mt-2" : "max-h-0 opacity-0 mt-0"
          }`}
        >
          <input 
            ref={inputRef}
            type="text" 
            placeholder="Search conversations..." 
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              if (e.target.value === "") {
                setShowSearch(false);
              }
            }}
            className="w-full bg-[#161b22] border border-[#30363d] rounded text-xs px-2 py-1.5 text-foreground focus:outline-none focus:border-primary transition-colors"
          />
        </div>
      </div>
      
      {filteredConversations.length === 0 ? (
        <div className="px-6 py-4 text-xs text-muted-foreground">
          {searchQuery ? "No matching conversations." : "No past conversations."}
        </div>
      ) : (
        <>
          {renderGroup("Today", todayConvs, true)}
          {renderGroup("Previous 7 Days", previousConvs, false)}
          {renderGroup("Older", olderConvs, false)}
          
          {hasMore && (
            <button 
              onClick={() => setVisibleCount(prev => prev + 10)}
              className="px-4 py-2 mx-2 text-xs text-muted-foreground hover:text-foreground text-left flex items-center transition-colors focus:outline-none"
            >
              Show more <span className="ml-1 text-[10px]">⌄</span>
            </button>
          )}
        </>
      )}
    </div>
  );
}
