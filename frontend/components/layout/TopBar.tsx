"use client";

import React, { useState } from 'react';
import { 
  Bell, 
  Sun, 
  ChevronDown,
  Search,
  Command
} from 'lucide-react';
import { ResponseMetadata } from '../../lib/types/models';

interface TopBarProps {
  title: string | null;
  subtitle?: string;
  metadata?: ResponseMetadata;
  onUpdateTitle?: (newTitle: string) => void;
}

export function TopBar({ title, subtitle, onUpdateTitle }: TopBarProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editTitle, setEditTitle] = useState("");

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
              className="flex items-center space-x-1 cursor-pointer hover:text-primary transition-colors text-sm font-semibold"
              onClick={handleTitleClick}
            >
              <span className="truncate">{title || "New Conversation"}</span>
              <ChevronDown className="h-4 w-4 text-muted-foreground" />
            </div>
          )
        )}
      </div>

      {/* Center: Global Search (Mocked) */}
      <div className="flex-1 max-w-md hidden md:block">
        <div className="relative group cursor-not-allowed">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Search className="h-4 w-4 text-muted-foreground group-hover:text-foreground transition-colors" />
          </div>
          <input 
            type="text" 
            placeholder="Search anything..." 
            disabled
            className="block w-full pl-10 pr-12 py-1.5 border border-[#30363d] rounded-md leading-5 bg-[#161b22] text-sm text-foreground placeholder-muted-foreground focus:outline-none focus:bg-background focus:border-primary transition-colors cursor-not-allowed" 
          />
          <div className="absolute inset-y-0 right-0 pr-2 flex items-center pointer-events-none">
            <div className="flex items-center space-x-1 bg-[#21262d] text-muted-foreground border border-[#30363d] rounded px-1.5 py-0.5 text-[10px] font-medium">
              <span>⌘</span>
              <span>K</span>
            </div>
          </div>
        </div>
      </div>

      {/* Right side controls */}
      <div className="flex-1 flex items-center justify-end space-x-4">
        <button className="text-muted-foreground hover:text-foreground transition-colors cursor-not-allowed" title="Theme toggle mocked">
          <Sun className="h-5 w-5" />
        </button>

        {/* System Healthy Pill */}
        <div className="hidden sm:flex items-center space-x-2 px-3 py-1 rounded-full bg-[#122822] text-xs font-medium border border-[#10b981]/20">
          <div className="h-2 w-2 rounded-full bg-[#10b981]" />
          <span className="text-foreground/90">System Healthy</span>
        </div>

        <div className="flex items-center space-x-4 ml-2">
          {/* Notification Bell */}
          <button className="relative text-muted-foreground hover:text-foreground transition-colors cursor-not-allowed">
            <Bell className="h-5 w-5" />
            <span className="absolute -top-1 -right-1 flex h-3.5 w-3.5">
              <span className="relative inline-flex rounded-full h-3.5 w-3.5 bg-red-500 text-[8px] font-bold text-white items-center justify-center border border-background">
                3
              </span>
            </span>
          </button>
          
          {/* Avatar */}
          <div className="h-8 w-8 rounded-full overflow-hidden flex-shrink-0 border border-[#30363d] cursor-pointer">
            <img src="https://i.pravatar.cc/150?u=admin" alt="Admin" className="h-full w-full object-cover" />
          </div>
        </div>
      </div>
      
    </div>
  );
}
