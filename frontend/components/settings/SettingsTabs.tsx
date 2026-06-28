"use client";

import React, { useState } from 'react';
import { Settings, Hexagon, Search, Users, Bell, Box, CreditCard } from 'lucide-react';

export function SettingsTabs() {
  const [activeTab, setActiveTab] = useState('General');

  const tabs = [
    { id: 'General', icon: Settings },
    { id: 'Models', icon: Hexagon },
    { id: 'Retrieval', icon: Search },
    { id: 'Users & Access', icon: Users },
    { id: 'Notifications', icon: Bell },
    { id: 'System', icon: Box },
    { id: 'Billing', icon: CreditCard },
  ];

  return (
    <div className="flex items-center space-x-1 border-b border-[#1e2329] overflow-x-auto scrollbar-none pb-px">
      {tabs.map((tab) => {
        const isActive = activeTab === tab.id;
        return (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center space-x-2 px-4 py-3 border-b-2 transition-colors whitespace-nowrap text-sm font-medium ${
              isActive 
                ? 'border-[#10b981] text-foreground' 
                : 'border-transparent text-muted-foreground hover:text-foreground hover:border-[#30363d]'
            }`}
          >
            <tab.icon className={`w-4 h-4 ${isActive ? 'text-primary' : 'text-muted-foreground'}`} />
            <span>{tab.id}</span>
          </button>
        );
      })}
    </div>
  );
}
