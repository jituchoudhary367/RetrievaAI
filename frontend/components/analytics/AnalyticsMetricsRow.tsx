"use client";

import React from 'react';
import { ArrowUp, ArrowDown } from 'lucide-react';

export function AnalyticsMetricsRow() {
  const MetricItem = ({ label, value, trend, trendUp }: any) => (
    <div className="flex flex-col space-y-1">
      <div className="flex items-center space-x-1">
        <span className="text-[10px] text-muted-foreground">{label}</span>
        <span className="text-[9px] text-muted-foreground w-3 h-3 rounded-full border border-[#30363d] inline-flex items-center justify-center cursor-help">i</span>
      </div>
      <span className="text-xl font-bold text-foreground">{value}</span>
      <div className={`flex items-center text-[9px] ${trendUp ? 'text-[#10b981]' : 'text-red-500'}`}>
        {trendUp ? <ArrowUp className="w-3 h-3 mr-0.5" /> : <ArrowDown className="w-3 h-3 mr-0.5" />}
        {trend}
      </div>
    </div>
  );

  const UserMetricItem = ({ icon: Icon, label, value, trend, trendUp }: any) => (
    <div className="flex flex-col space-y-2">
      <div className="flex items-center space-x-1.5 text-[10px] text-muted-foreground">
        <Icon className="w-3.5 h-3.5" />
        <span>{label}</span>
      </div>
      <span className="text-xl font-bold text-foreground">{value}</span>
      <div className={`flex items-center text-[9px] ${trendUp ? 'text-[#10b981]' : 'text-red-500'}`}>
        {trendUp ? <ArrowUp className="w-3 h-3 mr-0.5" /> : <ArrowDown className="w-3 h-3 mr-0.5" />}
        {trend}
      </div>
    </div>
  );

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      
      {/* Retrieval Performance */}
      <div className="bg-[#12181f] border border-[#1e2329] rounded-xl p-5 flex flex-col justify-between min-h-[140px]">
        <div className="flex flex-col space-y-1 mb-4">
          <span className="text-xs font-semibold text-foreground">Retrieval Performance</span>
          <span className="text-[10px] text-muted-foreground">Retrieval quality metrics</span>
        </div>
        
        <div className="flex items-center justify-between">
          <MetricItem label="Top 1 Accuracy" value="87.3%" trend="6.4%" trendUp={true} />
          <MetricItem label="MRR" value="0.76" trend="5.2%" trendUp={true} />
          <MetricItem label="Hit Rate@5" value="92.1%" trend="7.1%" trendUp={true} />
          <MetricItem label="NDCG@10" value="0.81" trend="4.8%" trendUp={true} />
        </div>
      </div>

      {/* User Engagement */}
      <div className="bg-[#12181f] border border-[#1e2329] rounded-xl p-5 flex flex-col justify-between min-h-[140px]">
        <div className="flex flex-col space-y-1 mb-4">
          <span className="text-xs font-semibold text-foreground">User Engagement</span>
          <span className="text-[10px] text-muted-foreground">User interaction metrics</span>
        </div>
        
        <div className="flex items-center justify-between">
          <UserMetricItem icon={() => <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>} label="Active Users" value="1,248" trend="15.3%" trendUp={true} />
          <UserMetricItem icon={() => <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="8.5" cy="7" r="4"></circle><line x1="20" y1="8" x2="20" y2="14"></line><line x1="23" y1="11" x2="17" y2="11"></line></svg>} label="New Users" value="342" trend="22.1%" trendUp={true} />
          <UserMetricItem icon={() => <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>} label="Conversations" value="2,184" trend="17.8%" trendUp={true} />
          <UserMetricItem icon={() => <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.2"></path></svg>} label="Avg. Turns" value="4.6" trend="9.7%" trendUp={true} />
        </div>
      </div>

    </div>
  );
}
