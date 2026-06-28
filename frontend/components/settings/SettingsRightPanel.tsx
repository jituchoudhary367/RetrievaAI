"use client";

import React from 'react';
import { User, Shield, Key, Lock, MonitorSmartphone, Link as LinkIcon, Database, Check, ChevronRight, Clock, UserPlus, KeyRound, Edit3, Hexagon, DatabaseBackup } from 'lucide-react';

export function SettingsRightPanel() {
  
  return (
    <div className="flex-1 flex flex-col p-6 space-y-8">
      
      {/* Account Information */}
      <div className="flex flex-col space-y-4">
        <span className="text-xs font-semibold text-foreground">Account Information</span>
        <div className="flex flex-col p-4 rounded-xl bg-[#12181f] border border-[#1e2329] space-y-4">
          <div className="flex items-start space-x-3">
            <div className="w-10 h-10 rounded-full bg-[#10b981]/10 border border-[#10b981]/20 flex flex-shrink-0 items-center justify-center">
              <User className="w-5 h-5 text-[#10b981]" strokeWidth={1.5} />
            </div>
            <div className="flex flex-col min-w-0">
              <div className="flex items-center space-x-2">
                <span className="text-sm font-semibold text-foreground truncate">Admin User</span>
                <span className="text-[9px] font-medium text-[#10b981] bg-[#10b981]/10 px-1.5 py-0.5 rounded border border-[#10b981]/20">Administrator</span>
              </div>
              <span className="text-[10px] text-muted-foreground truncate mt-0.5">admin@ragsystem.ai</span>
              <span className="text-[9px] text-muted-foreground mt-1">Last login: May 25, 2024, 10:24 AM</span>
            </div>
          </div>
          <button className="w-full flex items-center justify-center space-x-2 py-1.5 rounded-md border border-[#30363d] text-xs font-medium text-muted-foreground hover:text-foreground hover:bg-[#21262d] transition-colors">
            <Edit3 className="w-3.5 h-3.5" />
            <span>Edit Profile</span>
          </button>
        </div>
      </div>

      {/* Security Settings */}
      <div className="flex flex-col space-y-4 pb-6 border-b border-[#30363d]">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded bg-[#3b82f6]/10 border border-[#3b82f6]/20 flex items-center justify-center">
            <Shield className="w-4 h-4 text-[#3b82f6]" strokeWidth={1.5} />
          </div>
          <div className="flex flex-col">
            <span className="text-xs font-semibold text-foreground">Security Settings</span>
            <span className="text-[9px] text-muted-foreground">Manage your security preferences</span>
          </div>
        </div>
        
        <div className="flex flex-col space-y-1">
          <div className="flex items-center justify-between p-2 rounded hover:bg-[#12181f] transition-colors cursor-pointer group">
            <div className="flex items-center space-x-2">
              <div className="w-5 h-5 rounded bg-red-500/10 flex items-center justify-center">
                <MonitorSmartphone className="w-3 h-3 text-red-500" />
              </div>
              <span className="text-[11px] text-foreground">Two-Factor Authentication</span>
            </div>
            <div className="flex items-center space-x-1.5">
              <span className="text-[10px] text-[#10b981]">Enabled</span>
              <div className="w-3.5 h-3.5 rounded-full bg-[#10b981]/20 flex items-center justify-center">
                <Check className="w-2.5 h-2.5 text-[#10b981]" strokeWidth={3} />
              </div>
            </div>
          </div>

          {[
            { icon: Lock, iconColor: 'text-[#8b5cf6]', iconBg: 'bg-[#8b5cf6]/10', label: 'Password', sub: 'Last changed 15 days ago' },
            { icon: Key, iconColor: 'text-[#06b6d4]', iconBg: 'bg-[#06b6d4]/10', label: 'API Key', sub: 'Manage your API keys' },
            { icon: Shield, iconColor: 'text-[#10b981]', iconBg: 'bg-[#10b981]/10', label: 'Sessions', sub: 'Manage active sessions' },
          ].map((item, i) => (
            <div key={i} className="flex items-center justify-between p-2 rounded hover:bg-[#12181f] transition-colors cursor-pointer group">
              <div className="flex items-center space-x-2">
                <div className={`w-5 h-5 rounded flex items-center justify-center ${item.iconBg}`}>
                  <item.icon className={`w-3 h-3 ${item.iconColor}`} />
                </div>
                <div className="flex flex-col">
                  <span className="text-[11px] text-foreground">{item.label}</span>
                  <span className="text-[9px] text-muted-foreground">{item.sub}</span>
                </div>
              </div>
              <ChevronRight className="w-3.5 h-3.5 text-muted-foreground group-hover:text-foreground transition-colors" />
            </div>
          ))}
        </div>
        <button className="w-full flex items-center justify-center space-x-2 py-1.5 rounded-md border border-[#30363d] text-[11px] font-medium text-muted-foreground hover:text-foreground hover:bg-[#21262d] transition-colors mt-2">
          <Shield className="w-3 h-3" />
          <span>View Security Logs</span>
        </button>
      </div>

      {/* Integrations */}
      <div className="flex flex-col space-y-4 pb-6 border-b border-[#30363d]">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded bg-[#8b5cf6]/10 border border-[#8b5cf6]/20 flex items-center justify-center">
            <LinkIcon className="w-4 h-4 text-[#8b5cf6]" strokeWidth={1.5} />
          </div>
          <div className="flex flex-col">
            <span className="text-xs font-semibold text-foreground">Integrations</span>
            <span className="text-[9px] text-muted-foreground">Manage external integrations</span>
          </div>
        </div>
        
        <div className="flex flex-col space-y-1">
          {[
            { icon: Database, iconColor: 'text-[#10b981]', iconBg: 'bg-[#10b981]/10', label: 'Qdrant Vector DB' },
            { icon: DatabaseBackup, iconColor: 'text-red-500', iconBg: 'bg-red-500/10', label: 'Redis Cache' },
            { icon: Hexagon, iconColor: 'text-yellow-500', iconBg: 'bg-yellow-500/10', label: 'LLM API (Groq)' },
            { icon: Database, iconColor: 'text-[#3b82f6]', iconBg: 'bg-[#3b82f6]/10', label: 'Embedding API' },
          ].map((item, i) => (
            <div key={i} className="flex items-center justify-between p-2 rounded hover:bg-[#12181f] transition-colors cursor-pointer group">
              <div className="flex items-center space-x-2">
                <div className={`w-5 h-5 rounded flex items-center justify-center ${item.iconBg}`}>
                  <item.icon className={`w-3 h-3 ${item.iconColor}`} />
                </div>
                <span className="text-[11px] text-foreground">{item.label}</span>
              </div>
              <div className="flex items-center space-x-1.5">
                <span className="text-[9px] text-[#10b981]">Connected</span>
                <ChevronRight className="w-3.5 h-3.5 text-muted-foreground group-hover:text-foreground transition-colors" />
              </div>
            </div>
          ))}
        </div>
        <button className="w-full flex items-center justify-center space-x-2 py-1.5 rounded-md border border-[#30363d] text-[11px] font-medium text-muted-foreground hover:text-foreground hover:bg-[#21262d] transition-colors mt-2">
          <Settings className="w-3 h-3" />
          <span>Manage Integrations</span>
        </button>
      </div>

      {/* Recent Activity */}
      <div className="flex flex-col space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Clock className="w-3.5 h-3.5 text-[#3b82f6]" />
            <span className="text-xs font-semibold text-foreground">Recent Activity</span>
          </div>
          <span className="text-[10px] text-muted-foreground hover:text-foreground cursor-pointer">View all</span>
        </div>
        
        <div className="flex flex-col space-y-3">
          {[
            { icon: Settings, label: 'System configuration updated', time: '2 min ago' },
            { icon: UserPlus, label: 'New user added: johndoe@company.com', time: '1 hr ago' },
            { icon: KeyRound, label: 'API key generated', time: '3 hrs ago' },
            { icon: DatabaseBackup, label: 'Backup completed successfully', time: 'Yesterday' },
          ].map((act, i) => (
            <div key={i} className="flex items-center justify-between group">
              <div className="flex items-center space-x-2 min-w-0">
                <act.icon className="w-3 h-3 text-muted-foreground flex-shrink-0" />
                <span className="text-[10px] text-foreground truncate">{act.label}</span>
              </div>
              <span className="text-[9px] text-muted-foreground flex-shrink-0 ml-2">{act.time}</span>
            </div>
          ))}
        </div>
      </div>

    </div>
  );
}
