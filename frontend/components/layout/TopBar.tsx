"use client";

import React, { useState, useEffect, useRef } from 'react';
import { 
  Bell, 
  Sun, 
  ChevronDown,
  Search,
  Check
} from 'lucide-react';
import { ResponseMetadata } from '../../lib/types/models';
import { useHealthPolling } from '../../lib/hooks/useHealthPolling';
import { getUserInfo } from '../../lib/auth/session';
import { apiFetch } from '../../lib/api/client';
import { useRouter } from 'next/navigation';

interface TopBarProps {
  title: string | null;
  subtitle?: string;
  searchPlaceholder?: string;
  metadata?: ResponseMetadata;
  onUpdateTitle?: (newTitle: string) => void;
  editable?: boolean;
}

interface Notification {
  id: string;
  message: string;
  is_read: boolean;
  created_at: string;
}

export function TopBar({ title, subtitle, searchPlaceholder, onUpdateTitle, editable }: TopBarProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editTitle, setEditTitle] = useState("");
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [showNotifications, setShowNotifications] = useState(false);
  const [globalSearchQuery, setGlobalSearchQuery] = useState("");
  const notifRef = useRef<HTMLDivElement>(null);
  const { health, error: healthError } = useHealthPolling(30000);
  const userInfo = getUserInfo();
  const router = useRouter();

  // Poll notifications every 30s
  useEffect(() => {
    const fetchNotifications = async () => {
      try {
        const data = await apiFetch<{ items: Notification[]; total: number }>('/api/notifications', { method: 'GET' });
        setNotifications(data.items || []);
      } catch {
        // Not critical — silently ignore if endpoint unavailable
      }
    };
    fetchNotifications();
    const interval = setInterval(fetchNotifications, 30000);
    return () => clearInterval(interval);
  }, []);

  // Close notification dropdown on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (notifRef.current && !notifRef.current.contains(e.target as Node)) {
        setShowNotifications(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const unreadCount = notifications.filter(n => !n.is_read).length;

  const markRead = async (id: string) => {
    try {
      await apiFetch(`/api/notifications/${id}/read`, { method: 'POST' });
      setNotifications(prev => prev.map(n => n.id === id ? { ...n, is_read: true } : n));
    } catch {}
  };

  const handleTitleClick = () => {
    setEditTitle(title || "New Conversation");
    setIsEditing(true);
  };

  const handleTitleSubmit = () => {
    if (onUpdateTitle && editTitle.trim()) {
      onUpdateTitle(editTitle.trim());
    }
    setIsEditing(false);
  };

  // Determine health status for the pill
  const overallStatus = health?.status || (healthError ? 'unhealthy' : null);
  const healthPillClass = overallStatus === 'healthy'
    ? 'bg-[#122822] border-[#10b981]/20 text-foreground/90'
    : overallStatus === 'degraded'
    ? 'bg-yellow-900/20 border-yellow-500/20 text-yellow-400'
    : overallStatus === 'unhealthy'
    ? 'bg-red-900/20 border-red-500/20 text-red-400'
    : 'bg-[#161b22] border-[#30363d] text-muted-foreground';
  const healthDotClass = overallStatus === 'healthy'
    ? 'bg-[#10b981]'
    : overallStatus === 'degraded'
    ? 'bg-yellow-500'
    : overallStatus === 'unhealthy'
    ? 'bg-red-500'
    : 'bg-muted-foreground';
  const healthLabel = overallStatus === 'healthy'
    ? 'System Healthy'
    : overallStatus === 'degraded'
    ? 'Degraded'
    : overallStatus === 'unhealthy'
    ? 'System Issues'
    : 'Checking...';

  // Avatar: real Google picture, or initials fallback
  const avatarUrl = userInfo?.avatar_url;
  const displayName = userInfo?.name || userInfo?.email || 'U';
  const initials = displayName.charAt(0).toUpperCase();

  return (
    <div className="h-16 flex items-center justify-between px-6 border-b border-[#30363d] bg-background">
      
      {/* Left side: Title */}
      <div className="flex-1 min-w-0 pr-4 flex items-center">
        {isEditing ? (
          <input
            type="text"
            className="w-full max-w-sm bg-muted text-sm px-2 py-1 rounded border-none focus:ring-1 focus:ring-primary outline-none"
            value={editTitle}
            onChange={(e) => setEditTitle(e.target.value)}
            onBlur={handleTitleSubmit}
            onKeyDown={(e) => e.key === 'Enter' && handleTitleSubmit()}
            autoFocus
          />
        ) : (
          subtitle ? (
            <div className="flex flex-col">
              <span className="font-semibold text-lg leading-tight text-foreground">{title || "Search"}</span>
              <span className="text-xs text-muted-foreground">{subtitle}</span>
            </div>
          ) : (
            <div 
              className={`flex items-center space-x-1 text-sm font-semibold ${editable ? 'cursor-pointer hover:text-primary transition-colors' : ''}`}
              onClick={editable ? handleTitleClick : undefined}
            >
              <span className="truncate">{title || "New Conversation"}</span>
              {editable && <ChevronDown className="h-4 w-4 text-muted-foreground" />}
            </div>
          )
        )}
      </div>

      {/* Center: Global Search */}
      <div className="flex-1 max-w-md hidden md:block">
        <div className="relative group">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Search className="h-4 w-4 text-muted-foreground group-hover:text-foreground transition-colors" />
          </div>
          <input 
            type="text" 
            placeholder={searchPlaceholder || "Search anything..."} 
            value={globalSearchQuery}
            onChange={(e) => setGlobalSearchQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && globalSearchQuery.trim()) {
                router.push(`/search?q=${encodeURIComponent(globalSearchQuery.trim())}`);
              }
            }}
            className="block w-full pl-10 pr-12 py-1.5 border border-[#30363d] rounded-md leading-5 bg-[#161b22] text-sm text-foreground placeholder-muted-foreground focus:outline-none focus:bg-background focus:border-primary transition-colors" 
          />
          <div className="absolute inset-y-0 right-0 pr-2 flex items-center pointer-events-none">
            <div className="flex items-center space-x-1 bg-[#21262d] text-muted-foreground border border-[#30363d] rounded px-1.5 py-0.5 text-[10px] font-medium">
              <span>Enter</span>
            </div>
          </div>
        </div>
      </div>

      {/* Right side controls */}
      <div className="flex-1 flex items-center justify-end space-x-4">
        {/* System Health Pill — real status */}
        <div className={`hidden sm:flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-medium border ${healthPillClass}`}>
          <div className={`h-2 w-2 rounded-full ${healthDotClass}`} />
          <span>{healthLabel}</span>
        </div>

        <div className="flex items-center space-x-4 ml-2">
          {/* Notification Bell — real unread count */}
          <div className="relative" ref={notifRef}>
            <button
              className="relative text-muted-foreground hover:text-foreground transition-colors"
              onClick={() => setShowNotifications(prev => !prev)}
            >
              <Bell className="h-5 w-5" />
              {unreadCount > 0 && (
                <span className="absolute -top-1 -right-1 flex h-3.5 w-3.5">
                  <span className="relative inline-flex rounded-full h-3.5 w-3.5 bg-red-500 text-[8px] font-bold text-white items-center justify-center border border-background">
                    {unreadCount > 9 ? '9+' : unreadCount}
                  </span>
                </span>
              )}
            </button>

            {/* Notification Dropdown */}
            {showNotifications && (
              <div className="absolute right-0 top-8 z-50 w-80 bg-[#12181f] border border-[#30363d] rounded-xl shadow-xl overflow-hidden">
                <div className="px-4 py-3 border-b border-[#30363d] flex items-center justify-between">
                  <span className="text-xs font-semibold text-foreground">Notifications</span>
                  {unreadCount > 0 && (
                    <span className="text-[10px] text-muted-foreground">{unreadCount} unread</span>
                  )}
                </div>
                <div className="max-h-64 overflow-y-auto">
                  {notifications.length === 0 ? (
                    <div className="px-4 py-6 text-center text-xs text-muted-foreground">No notifications</div>
                  ) : (
                    notifications.map(notif => (
                      <div
                        key={notif.id}
                        className={`px-4 py-3 border-b border-[#1e2329] flex items-start justify-between gap-2 hover:bg-[#1a212a] transition-colors ${notif.is_read ? 'opacity-60' : ''}`}
                      >
                        <div className="flex items-start gap-2 flex-1 min-w-0">
                          {!notif.is_read && (
                            <div className="w-1.5 h-1.5 rounded-full bg-[#10b981] mt-1.5 flex-shrink-0" />
                          )}
                          <span className="text-[11px] text-foreground leading-relaxed">{notif.message}</span>
                        </div>
                        {!notif.is_read && (
                          <button
                            onClick={() => markRead(notif.id)}
                            className="flex-shrink-0 text-muted-foreground hover:text-[#10b981] transition-colors"
                            title="Mark as read"
                          >
                            <Check className="h-3.5 w-3.5" />
                          </button>
                        )}
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>
          
          {/* Avatar — real user photo or initials */}
          <div className="h-8 w-8 rounded-full overflow-hidden flex-shrink-0 border border-[#30363d] cursor-pointer bg-[#21262d] flex items-center justify-center">
            {avatarUrl ? (
              <img src={avatarUrl} alt={displayName} className="h-full w-full object-cover" />
            ) : (
              <span className="text-xs font-bold text-foreground">{initials}</span>
            )}
          </div>
        </div>
      </div>
      
    </div>
  );
}
