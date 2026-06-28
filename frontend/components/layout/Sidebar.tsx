"use client";

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  MessageSquare, 
  Search, 
  FileText, 
  DownloadCloud, 
  BarChart2, 
  Wrench, 
  Settings,
  ChevronDown,
  Hexagon,
  Plus
} from 'lucide-react';
import { ConversationList } from './ConversationList';
import { useConversations } from '../../lib/hooks/useConversations';
import { StatusBar } from './StatusBar';

export function Sidebar({ 
  conversationsContext 
}: { 
  conversationsContext?: ReturnType<typeof useConversations> 
}) {
  const pathname = usePathname();
  const fallbackContext = useConversations();
  const { conversations, activeConversation, startNew, selectConversation } = 
    conversationsContext || fallbackContext;

  const activeId = activeConversation?.sessionId || null;

  const NavItem = ({ href, icon: Icon, label, disabled = false }) => {
    const isActive = pathname === href;
    return (
      <Link 
        href={disabled ? "#" : href}
        className={`flex items-center px-4 py-2.5 text-sm font-medium transition-colors border-l-2 ${
          isActive && !disabled 
            ? 'border-[#10b981] bg-[#1a212a] text-[#e6edf3]' 
            : 'border-transparent text-muted-foreground hover:bg-muted/50 hover:text-foreground'
        } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
        title={disabled ? "Coming soon" : undefined}
      >
        <Icon className={`mr-3 h-4 w-4 ${isActive ? 'text-[#10b981]' : ''}`} />
        <span className="flex-1">{label}</span>
      </Link>
    );
  };

  return (
    <div className="w-64 bg-[#0d1117] border-r border-[#30363d] flex flex-col h-full flex-shrink-0">
      {/* Brand */}
      <div className="h-16 flex items-center px-4 mb-2 mt-2">
        <div className="flex items-center justify-center relative w-8 h-8 mr-3">
          <Hexagon className="w-8 h-8 text-[#10b981] absolute fill-[#10b981]/20" />
          <div className="w-2 h-2 bg-[#10b981] rounded-full relative z-10" />
        </div>
        <div className="flex flex-col">
          <span className="font-bold tracking-wide text-foreground text-sm uppercase">RAG System</span>
          <span className="text-[10px] text-muted-foreground tracking-widest uppercase">Production-Ready</span>
        </div>
      </div>

      {/* New Chat Button */}
      <div className="px-4 mb-6">
        <button 
          onClick={startNew}
          className="w-full flex items-center justify-between bg-[#122822] text-[#10b981] hover:bg-[#1a382f] border border-[#10b981]/20 px-3 py-2 rounded-md transition-colors"
        >
          <div className="flex items-center text-sm font-medium">
            <Plus className="h-4 w-4 mr-2" />
            <span>New Conversation</span>
          </div>
          <div className="flex items-center space-x-0.5 text-[10px] bg-[#0d1117] border border-[#10b981]/30 px-1.5 py-0.5 rounded text-[#10b981]">
            <span>⌘</span>
            <span>N</span>
          </div>
        </button>
      </div>

      {/* Primary Nav */}
      <div className="space-y-0.5 mb-6">
        <NavItem href="/" icon={MessageSquare} label="Chat" />
        <NavItem href="/search" icon={Search} label="Search" />
        <NavItem href="/documents" icon={FileText} label="Documents" />
        <NavItem href="/ingestion" icon={DownloadCloud} label="Ingestion" />
        <NavItem href="/analytics" icon={BarChart2} label="Analytics" />
        <NavItem href="/tools" icon={Wrench} label="Tools" />
        <NavItem href="/settings" icon={Settings} label="Settings" disabled />
      </div>

      {/* Conversations List */}
      <div className="flex-1 overflow-hidden flex flex-col">
        <ConversationList 
          conversations={conversations} 
          activeId={activeId} 
          onSelect={selectConversation} 
        />
      </div>

      {/* User Identity */}
      <div className="flex-shrink-0 px-4 py-3 mx-4 mt-2 border border-[#30363d] rounded-lg flex items-center justify-between hover:bg-muted/30 transition-colors cursor-pointer bg-[#161b22]">
        <div className="flex items-center space-x-3 overflow-hidden">
          <div className="h-8 w-8 rounded-full overflow-hidden flex-shrink-0">
            <img src="https://i.pravatar.cc/150?u=admin" alt="Admin" className="h-full w-full object-cover" />
          </div>
          <div className="flex flex-col overflow-hidden">
            <span className="text-sm font-semibold truncate text-foreground">Admin User</span>
            <span className="text-xs text-muted-foreground truncate">admin@ragsystem.ai</span>
          </div>
        </div>
        <ChevronDown className="h-4 w-4 text-muted-foreground flex-shrink-0" />
      </div>

      {/* Status Bar inside Sidebar */}
      <StatusBar />
    </div>
  );
}
