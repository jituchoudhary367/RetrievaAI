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
import { getAuthToken, clearAuthToken, getRoles, getUserInfo } from '../../lib/auth/session';
import { useRouter } from 'next/navigation';
import { useState, useEffect } from 'react';

export function Sidebar({ 
  conversationsContext 
}: { 
  conversationsContext?: ReturnType<typeof useConversations> 
}) {
  const pathname = usePathname();
  const router = useRouter();
  const fallbackContext = useConversations();
  const { conversations, activeConversation, startNew, selectConversation } = 
    conversationsContext || fallbackContext;

  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [userRoles, setUserRoles] = useState<string[]>([]);
  const [userInfo, setUserInfo] = useState<{name: string, avatarUrl: string} | null>(null);
  const [showDropdown, setShowDropdown] = useState(false);

  useEffect(() => {
    const token = getAuthToken();
    if (token) {
      setIsAuthenticated(true);
      setUserRoles(getRoles());
      setUserInfo(getUserInfo());
    } else {
      setIsAuthenticated(false);
      setUserRoles([]);
      setUserInfo(null);
    }
  }, [pathname]);

  const handleLogout = () => {
    clearAuthToken();
    setIsAuthenticated(false);
    setUserRoles([]);
    setUserInfo(null);
    router.push('/login');
  };

  const activeId = activeConversation?.sessionId || null;

  const NavItem = ({ href, icon: Icon, label, disabled = false }: { href: string, icon: any, label: string, disabled?: boolean }) => {
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
        <img src="/logo.ico" alt="RetrievaAI Logo" className="w-12 h-12 object-contain mr-3 drop-shadow-md" />
        <span className="font-bold tracking-wide text-foreground text-base uppercase" style={{ color: '#10b981' }}>RetrievaAI</span>
      </div>

      {/* New Chat Button */}
      <div className="px-4 mb-6">
        <button 
          onClick={() => { startNew(); router.push('/chat'); }}
          className="w-full flex items-center justify-between bg-[#122822] text-[#10b981] hover:bg-[#1a382f] border border-[#10b981]/20 px-3 py-2 rounded-md transition-colors"
        >
          <div className="flex items-center text-sm font-medium">
            <Plus className="h-4 w-4 mr-2" />
            <span>New Conversation</span>
          </div>
        </button>
      </div>

      {/* Primary Nav */}
      <div className="space-y-0.5 mb-6">
        <NavItem href="/chat" icon={MessageSquare} label="Chat" />
        <NavItem href="/search" icon={Search} label="Search" />
        <NavItem href="/documents" icon={FileText} label="Documents" />
        <NavItem href="/ingestion" icon={DownloadCloud} label="Ingestion" />
        <NavItem href="/analytics" icon={BarChart2} label="Analytics" />
        <NavItem href="/tools" icon={Wrench} label="Tools" />
        <NavItem href="/settings" icon={Settings} label="Settings" />
      </div>

      {/* Conversations List */}
      <div className="flex-1 overflow-hidden flex flex-col">
        <ConversationList 
          conversations={conversations} 
          activeId={activeId} 
          onSelect={(id) => { selectConversation(id); router.push('/chat'); }} 
        />
      </div>


    </div>
  );
}
