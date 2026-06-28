import React from 'react';
import { ConversationSummary } from '../../lib/storage/conversationStore';
import { Search, Filter } from 'lucide-react';

export function ConversationList({ 
  conversations, 
  activeId, 
  onSelect 
}: { 
  conversations: ConversationSummary[]; 
  activeId: string | null; 
  onSelect: (id: string) => void;
}) {
  const today = new Date().setHours(0,0,0,0);
  const sevenDaysAgo = new Date(today - 7 * 24 * 60 * 60 * 1000);
  
  const todayConvs = conversations.filter(c => c.updatedAt >= today);
  const previousConvs = conversations.filter(c => c.updatedAt >= sevenDaysAgo && c.updatedAt < today);
  const olderConvs = conversations.filter(c => c.updatedAt < sevenDaysAgo);

  const formatTime = (ts: number) => {
    return new Intl.DateTimeFormat('en-US', { hour: '2-digit', minute: '2-digit' }).format(new Date(ts));
  };
  const formatDate = (ts: number) => {
    return new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric' }).format(new Date(ts));
  };

  const renderGroup = (title: string, list: ConversationSummary[], isToday: boolean) => {
    if (list.length === 0) return null;
    return (
      <div className="mb-4 px-2">
        <h4 className="px-2 text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-2">
          {title}
        </h4>
        <ul className="space-y-0.5">
          {list.map(c => {
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

  return (
    <div className="flex-1 overflow-y-auto py-2 scrollbar-thin flex flex-col">
      <div className="px-4 py-2 flex items-center justify-between text-muted-foreground mb-2">
        <span className="text-[10px] font-bold tracking-widest uppercase">Conversations</span>
        <div className="flex space-x-2">
          <Search className="h-3.5 w-3.5 cursor-not-allowed hover:text-foreground transition-colors" />
          <Filter className="h-3.5 w-3.5 cursor-not-allowed hover:text-foreground transition-colors" />
        </div>
      </div>
      
      {conversations.length === 0 ? (
        <div className="px-6 py-4 text-xs text-muted-foreground">
          No past conversations.
        </div>
      ) : (
        <>
          {renderGroup("Today", todayConvs, true)}
          {renderGroup("Previous 7 Days", previousConvs, false)}
          {renderGroup("Older", olderConvs, false)}
          
          <button className="px-4 py-2 mx-2 text-xs text-muted-foreground hover:text-foreground text-left flex items-center">
            Show more <span className="ml-1 text-[10px]">⌄</span>
          </button>
        </>
      )}
    </div>
  );
}
