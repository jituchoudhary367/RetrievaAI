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
        <div className="flex items-center justify-center relative w-8 h-8 mr-3">
          <img src="/logo.png" alt="RetrievaAI Logo" className="w-8 h-8 object-contain drop-shadow-md" />
        </div>
        <div className="flex flex-col">
          <span className="font-bold tracking-wide text-foreground text-sm uppercase">RetrievaAI</span>
          <span className="text-[10px] text-muted-foreground tracking-widest uppercase">Retrieve. Understand. Generate.</span>
        </div>
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

      {/* User Identity */}
      {isAuthenticated ? (
        <div className="relative mx-4 mt-2 mb-2 flex-shrink-0">
          <div 
            className="px-4 py-3 border border-[#30363d] rounded-lg flex items-center justify-between hover:bg-muted/30 transition-colors cursor-pointer bg-[#161b22]" 
            onClick={() => setShowDropdown(!showDropdown)} 
            title="Profile menu"
          >
            <div className="flex items-center space-x-3 overflow-hidden">
              {userInfo?.avatarUrl ? (
                <img src={userInfo.avatarUrl} alt="Avatar" className="h-8 w-8 rounded-full flex-shrink-0 object-cover" />
              ) : (
                <div className="h-8 w-8 rounded-full overflow-hidden flex-shrink-0 bg-[#10b981] flex items-center justify-center text-white font-bold">
                  {userRoles.includes('admin') ? 'A' : 'U'}
                </div>
              )}
              <div className="flex flex-col overflow-hidden">
                <span className="text-sm font-semibold truncate text-foreground">{userInfo?.name || 'Logged in'}</span>
                <span className="text-xs text-muted-foreground truncate">{userRoles.join(', ')}</span>
              </div>
            </div>
            <ChevronDown className="h-4 w-4 text-muted-foreground flex-shrink-0" />
          </div>
          
          {showDropdown && (
            <div className="absolute bottom-full left-0 mb-2 w-full bg-[#161b22] border border-[#30363d] rounded-lg shadow-lg overflow-hidden z-50">
              <button 
                onClick={handleLogout} 
                className="w-full text-left px-4 py-3 text-sm text-red-500 hover:bg-muted/50 transition-colors flex items-center"
              >
                Log out
              </button>
            </div>
          )}
        </div>
      ) : (
        <div className="px-4 mt-2 mb-2 flex space-x-2">
          <Link href="/login" className="flex-1 text-center bg-muted hover:bg-muted/80 text-foreground py-2 rounded-md text-sm font-medium transition-colors">
            Log in
          </Link>
          <Link href="/signup" className="flex-1 text-center bg-[#10b981] hover:bg-[#059669] text-white py-2 rounded-md text-sm font-medium transition-colors">
            Sign up
          </Link>
        </div>
      )}

      {/* Status Bar inside Sidebar */}
      <StatusBar />
    </div>
  );
}
