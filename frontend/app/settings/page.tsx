"use client";

import React from 'react';
import { TopBar } from '../../components/layout/TopBar';
import { SettingsTabs } from '../../components/settings/SettingsTabs';
import { SettingsGrid } from '../../components/settings/SettingsGrid';
import { DangerZone } from '../../components/settings/DangerZone';
import { SettingsRightPanel } from '../../components/settings/SettingsRightPanel';

export default function SettingsPage() {
  return (
    <div className="flex flex-col h-full w-full bg-background overflow-hidden">
      <TopBar 
        title="Settings"
        subtitle="Manage your system preferences and configurations"
      />

      <div className="flex-1 flex min-h-0">
        {/* Center Area */}
        <div className="flex-1 overflow-y-auto scrollbar-thin bg-background relative">
          <div className="flex flex-col p-6 lg:p-8 gap-6 max-w-[1400px] mx-auto w-full">
            <SettingsTabs />
            <SettingsGrid />
            <DangerZone />
          </div>
        </div>

        {/* Right Sidebar */}
        <div className="w-80 lg:w-[340px] flex-shrink-0 bg-[#0d1117] overflow-y-auto hidden xl:flex flex-col border-l border-[#30363d]">
           <SettingsRightPanel />
        </div>
      </div>
    </div>
  );
}
