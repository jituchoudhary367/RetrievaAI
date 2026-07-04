"use client";

import React, { useEffect, useState } from 'react';
import { MessageSquare, CheckCircle, Clock, Database, DollarSign, ArrowUp, ArrowDown } from 'lucide-react';
import { analyticsApi, AnalyticsOverview } from '../../lib/api/analytics';

export function AnalyticsStatsRow() {
  const [stats, setStats] = useState<AnalyticsOverview | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadStats() {
      try {
        const data = await analyticsApi.getOverview();
        setStats(data);
      } catch (e) {
        console.error("Failed to load overview stats", e);
      } finally {
        setLoading(false);
      }
    }
    loadStats();
    const interval = setInterval(loadStats, 5000);
    return () => clearInterval(interval);
  }, []);

  const StatCard = ({ title, value, subtext, subtextColor, subtextIcon: SubIcon, icon: Icon, colorClass, iconBg, svgPath, svgGradient }: any) => (
    <div className="flex-1 bg-[#12181f] border border-[#1e2329] rounded-xl p-4 hover:border-[#30363d] transition-colors relative overflow-hidden flex flex-col justify-between min-h-[110px]">
      <div className="flex items-start justify-between relative z-10">
        <div className="flex flex-col space-y-1">
          <span className="text-[10px] font-medium text-muted-foreground">{title}</span>
          <span className="text-xl font-bold text-foreground tracking-tight">{value}</span>
          <div className={`flex items-center text-[9px] mt-1 ${subtextColor}`}>
            {SubIcon && <SubIcon className="w-3 h-3 mr-1" />}
            {subtext}
          </div>
        </div>
        <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${iconBg} ${colorClass}`}>
          <Icon className="h-4 w-4" strokeWidth={1.5} />
        </div>
      </div>
      
      {/* Background Sparkline Mock */}
      <div className="absolute bottom-0 left-0 right-0 h-10 w-full opacity-60">
        <svg viewBox="0 0 100 30" className="w-full h-full" preserveAspectRatio="none">
          <defs>
            <linearGradient id={`grad-${title.replace(/ /g, '-')}`} x1="0" y1="0" x2="0" y2="1">
              {svgGradient}
            </linearGradient>
          </defs>
          <path 
            d={svgPath}
            fill="none" 
            stroke={`url(#grad-${title.replace(/ /g, '-')})`} 
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            className={`drop-shadow-[0_2px_4px_${colorClass.replace('text-', '')}]`}
          />
        </svg>
      </div>
    </div>
  );

  if (loading) {
    return <div className="animate-pulse h-[110px] bg-[#12181f] rounded-xl border border-[#1e2329] w-full" />;
  }

  const defaultStats: AnalyticsOverview = {
    totalQueries: 0,
    avgLatencyMs: 0,
    activeUsers: 0,
    documentsIndexed: 0,
    totalChunks: 0,
  };

  const current = stats || defaultStats;

  return (
    <div className="flex flex-col sm:flex-row w-full gap-4">
      <StatCard 
        title="Total Queries" 
        value={current.totalQueries.toLocaleString()} 
        subtext="Total usage in time range"
        subtextColor="text-muted-foreground"
        icon={MessageSquare}
        colorClass="text-[#10b981]"
        iconBg="bg-[#10b981]/10"
        svgPath="M 0 25 L 20 22 L 35 15 L 50 18 L 65 10 L 80 8 L 100 12"
        svgGradient={<><stop offset="0%" stopColor="#10b981" /><stop offset="100%" stopColor="#047857" /></>}
      />
      <StatCard 
        title="Active Users" 
        value={current.activeUsers.toLocaleString()} 
        subtext="Unique users"
        subtextColor="text-muted-foreground"
        icon={CheckCircle}
        colorClass="text-[#3b82f6]"
        iconBg="bg-[#3b82f6]/10"
        svgPath="M 0 20 L 15 15 L 30 18 L 45 10 L 60 12 L 75 5 L 100 8"
        svgGradient={<><stop offset="0%" stopColor="#3b82f6" /><stop offset="100%" stopColor="#1d4ed8" /></>}
      />
      <StatCard 
        title="Avg. Response Time" 
        value={`${(current.avgLatencyMs / 1000).toFixed(2)}s`} 
        subtext="End-to-end latency"
        subtextColor="text-muted-foreground"
        icon={Clock}
        colorClass="text-[#8b5cf6]"
        iconBg="bg-[#8b5cf6]/10"
        svgPath="M 0 10 L 20 15 L 35 12 L 50 20 L 65 18 L 80 25 L 100 22"
        svgGradient={<><stop offset="0%" stopColor="#8b5cf6" /><stop offset="100%" stopColor="#6d28d9" /></>}
      />
      <StatCard 
        title="Documents Indexed" 
        value={current.documentsIndexed?.toLocaleString() || '0'} 
        subtext={`${current.totalChunks?.toLocaleString() || '0'} Total Chunks`}
        subtextColor="text-muted-foreground"
        icon={Database}
        colorClass="text-yellow-500"
        iconBg="bg-yellow-500/10"
        svgPath="M 0 25 L 25 15 L 45 18 L 60 10 L 80 12 L 100 5"
        svgGradient={<><stop offset="0%" stopColor="#eab308" /><stop offset="100%" stopColor="#a16207" /></>}
      />
    </div>
  );
}
