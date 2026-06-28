"use client";

import React from 'react';
import { TopBar } from '../../components/layout/TopBar';
import { AnalyticsStatsRow } from '../../components/analytics/AnalyticsStatsRow';
import { AnalyticsChartsGrid } from '../../components/analytics/AnalyticsChartsGrid';
import { AnalyticsMetricsRow } from '../../components/analytics/AnalyticsMetricsRow';
import { AnalyticsRightPanel } from '../../components/analytics/AnalyticsRightPanel';
import { Calendar, Download, ChevronDown } from 'lucide-react';

export default function AnalyticsPage() {
  return (
    <div className="flex flex-col h-full w-full bg-background overflow-hidden">
      
      <TopBar 
        title="Analytics"
        subtitle="Track usage, performance and system insights"
      />

      <div className="flex-1 flex min-h-0">
        {/* Center Area (Stats & Charts) */}
        <div className="flex-1 overflow-y-auto scrollbar-thin bg-background relative">
          <div className="flex flex-col p-6 lg:p-8 gap-6 max-w-[1400px] mx-auto w-full">
            
            {/* Date Controls */}
            <div className="flex items-center justify-end space-x-3 w-full">
              <div className="flex items-center bg-[#12181f] border border-[#30363d] rounded-md px-3 py-1.5 text-xs text-muted-foreground hover:text-foreground hover:border-[#4b5563] transition-colors cursor-pointer">
                <span>May 19, 2024 - May 25, 2024</span>
                <Calendar className="h-3.5 w-3.5 ml-3" />
              </div>
              <div className="flex items-center bg-[#12181f] border border-[#30363d] rounded-md px-3 py-1.5 text-xs text-muted-foreground hover:text-foreground hover:border-[#4b5563] transition-colors cursor-pointer">
                <Download className="h-3.5 w-3.5 mr-2" />
                <span>Custom</span>
                <ChevronDown className="h-3 w-3 ml-2" />
              </div>
            </div>

            <AnalyticsStatsRow />
            <AnalyticsChartsGrid />
            <AnalyticsMetricsRow />
            
          </div>
        </div>

        {/* Right Sidebar (System Health, Top Lists, Costs) */}
        <div className="w-80 lg:w-[340px] flex-shrink-0 bg-[#0d1117] overflow-y-auto hidden md:flex flex-col border-l border-[#30363d]">
           <AnalyticsRightPanel />
        </div>
      </div>
    </div>
  );
}
