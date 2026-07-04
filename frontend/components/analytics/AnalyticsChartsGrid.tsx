"use client";

import React from 'react';
import { ChevronDown } from 'lucide-react';

interface SeriesPoint {
  date: string;
  count: number;
}

interface DistributionItem {
  intent: string;
  count: number;
}

interface Props {
  querySeries: SeriesPoint[];
  queryDistribution: DistributionItem[];
}

const DIST_COLORS = ['#10b981', '#3b82f6', '#8b5cf6', '#f97316', '#9ca3af'];

// Convert a series of {date, count} into SVG path points in a 100x100 viewBox
function seriesToSvgPath(series: SeriesPoint[]): { path: string; points: { x: number; y: number }[] } {
  if (series.length === 0) return { path: '', points: [] };
  const max = Math.max(...series.map(s => s.count), 1);
  const points = series.map((s, i) => ({
    x: series.length === 1 ? 50 : (i / (series.length - 1)) * 100,
    y: 100 - (s.count / max) * 90 - 5, // 5% padding top/bottom
  }));
  const path = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ');
  return { path, points };
}

function EmptyChart({ label }: { label: string }) {
  return (
    <div className="absolute inset-0 flex flex-col items-center justify-center text-muted-foreground">
      <span className="text-[10px]">No {label} yet</span>
      <span className="text-[9px] mt-1 opacity-60">Data will appear after first query</span>
    </div>
  );
}

export function AnalyticsChartsGrid({ querySeries, queryDistribution }: Props) {
  const { path: queryPath, points: queryPoints } = seriesToSvgPath(querySeries);

  // Build distribution donut from real data
  const totalDist = queryDistribution.reduce((s, d) => s + d.count, 0);
  let donutOffset = 0;
  const donutSegments = queryDistribution.map((d, i) => {
    const pct = totalDist > 0 ? (d.count / totalDist) * 100 : 0;
    const seg = { ...d, pct, color: DIST_COLORS[i % DIST_COLORS.length], offset: donutOffset };
    donutOffset += pct;
    return seg;
  });

  // X-axis labels from real dates
  const xLabels = querySeries.map(s => {
    const d = new Date(s.date);
    return `${d.toLocaleString('default', { month: 'short' })} ${d.getDate()}`;
  });

  const ChartHeader = ({ title, controls }: any) => (
    <div className="flex items-center justify-between mb-4">
      <span className="text-xs font-semibold text-foreground">{title}</span>
      <div className="flex items-center space-x-2">
        {controls.map((ctrl: string) => (
          <div key={ctrl} className="flex items-center space-x-1 cursor-pointer text-muted-foreground hover:text-foreground transition-colors text-[10px]">
            <span>{ctrl}</span>
            <ChevronDown className="h-3 w-3" />
          </div>
        ))}
      </div>
    </div>
  );

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      
      {/* Queries Over Time — real series */}
      <div className="lg:col-span-2 bg-[#12181f] border border-[#1e2329] rounded-xl p-5 flex flex-col min-h-[280px]">
        <ChartHeader title="Queries Over Time" controls={['Line', 'Daily']} />
        <span className="text-[10px] text-muted-foreground -mt-3 mb-6 block">Number of queries over time</span>
        
        <div className="flex-1 relative w-full h-full flex flex-col justify-between pt-2">
          <div className="absolute left-8 right-4 top-2 bottom-6">
            <div className="w-full h-full flex flex-col justify-between border-b border-[#30363d]">
              {[0,1,2,3,4].map(i => <div key={i} className="w-full h-[1px] bg-[#30363d]/30" />)}
            </div>
            
            {querySeries.length === 0 ? (
              <EmptyChart label="query data" />
            ) : (
              <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="absolute inset-0 w-full h-full overflow-visible">
                <path
                  d={queryPath}
                  fill="none"
                  stroke="#10b981"
                  strokeWidth="2"
                  vectorEffect="non-scaling-stroke"
                  className="drop-shadow-[0_4px_8px_rgba(16,185,129,0.5)]"
                />
                <path
                  d={`${queryPath} L 100 100 L 0 100 Z`}
                  fill="url(#grad-queries)"
                  vectorEffect="non-scaling-stroke"
                  className="opacity-20"
                />
                <defs>
                  <linearGradient id="grad-queries" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#10b981" stopOpacity="1" />
                    <stop offset="100%" stopColor="#10b981" stopOpacity="0" />
                  </linearGradient>
                </defs>
                {queryPoints.map((p, i) => (
                  <circle key={i} cx={`${p.x}%`} cy={`${p.y}%`} r="4" className="fill-[#10b981] stroke-background stroke-[2px]" />
                ))}
              </svg>
            )}
          </div>

          <div className="absolute bottom-0 left-8 right-4 flex justify-between text-[10px] text-muted-foreground mt-2">
            {xLabels.length > 0
              ? xLabels.map((label, i) => <span key={i}>{label}</span>)
              : ['Day 1','Day 2','Day 3','Day 4','Day 5','Day 6','Day 7'].map((d, i) => <span key={i} className="opacity-30">{d}</span>)
            }
          </div>
        </div>
      </div>

      {/* Query Type Distribution — real data */}
      <div className="bg-[#12181f] border border-[#1e2329] rounded-xl p-5 flex flex-col min-h-[280px]">
        <span className="text-xs font-semibold text-foreground mb-6 block">Query Type Distribution</span>
        
        <div className="flex-1 flex items-center justify-center">
          <div className="relative w-32 h-32 flex-shrink-0">
            <svg viewBox="0 0 100 100" className="w-full h-full transform -rotate-90">
              <circle cx="50" cy="50" r="40" fill="transparent" stroke="#1e2329" strokeWidth="16" />
              {queryDistribution.length === 0 ? (
                <circle cx="50" cy="50" r="40" fill="transparent" stroke="#1e2329" strokeWidth="16" />
              ) : (
                donutSegments.map((seg, i) => (
                  <circle
                    key={i}
                    cx="50" cy="50" r="40" fill="transparent"
                    stroke={seg.color}
                    strokeWidth="16"
                    strokeDasharray={`${seg.pct * 2.51} 251`}
                    strokeDashoffset={`-${seg.offset * 2.51}`}
                  />
                ))
              )}
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
              <span className="text-sm font-bold text-foreground">{totalDist.toLocaleString()}</span>
              <span className="text-[10px] text-muted-foreground">Total</span>
            </div>
          </div>
          
          <div className="ml-6 flex flex-col space-y-3 w-full">
            {queryDistribution.length === 0 ? (
              <span className="text-[10px] text-muted-foreground">No query data yet</span>
            ) : (
              donutSegments.map((seg, i) => (
                <div key={i} className="flex items-center justify-between text-[10px]">
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 rounded-full" style={{ backgroundColor: seg.color }} />
                    <span className="text-muted-foreground capitalize">{seg.intent.replace(/_/g, ' ')}</span>
                  </div>
                  <span className="text-foreground">{totalDist > 0 ? `${seg.pct.toFixed(1)}%` : '—'}</span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

    </div>
  );
}
