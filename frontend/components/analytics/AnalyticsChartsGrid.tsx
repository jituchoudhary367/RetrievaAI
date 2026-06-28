"use client";

import React from 'react';
import { ChevronDown } from 'lucide-react';

export function AnalyticsChartsGrid() {
  
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
      
      {/* Queries Over Time (Span 2) */}
      <div className="lg:col-span-2 bg-[#12181f] border border-[#1e2329] rounded-xl p-5 flex flex-col min-h-[280px]">
        <ChartHeader title="Queries Over Time" controls={['Line', 'Daily']} />
        <span className="text-[10px] text-muted-foreground -mt-3 mb-6 block">Number of queries over time</span>
        
        <div className="flex-1 relative w-full h-full flex flex-col justify-between pt-2">
          {/* Y Axis Labels */}
          <div className="absolute left-0 top-0 bottom-6 flex flex-col justify-between text-[10px] text-muted-foreground">
            <span>2.5K</span>
            <span>2K</span>
            <span>1.5K</span>
            <span>1K</span>
            <span>500</span>
            <span>0</span>
          </div>
          
          {/* Graph Area */}
          <div className="absolute left-8 right-4 top-2 bottom-6">
            {/* Grid Lines */}
            <div className="w-full h-full flex flex-col justify-between border-b border-[#30363d]">
              {[0,1,2,3,4].map(i => (
                <div key={i} className="w-full h-[1px] bg-[#30363d]/30" />
              ))}
            </div>
            
            {/* SVG Line Chart */}
            <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="absolute inset-0 w-full h-full overflow-visible">
              <path 
                d="M 0 50 L 16 35 L 33 55 L 50 38 L 66 45 L 83 15 L 100 20" 
                fill="none" 
                stroke="#10b981" 
                strokeWidth="2" 
                vectorEffect="non-scaling-stroke"
                className="drop-shadow-[0_4px_8px_rgba(16,185,129,0.5)]"
              />
              <path 
                d="M 0 50 L 16 35 L 33 55 L 50 38 L 66 45 L 83 15 L 100 20 L 100 100 L 0 100 Z" 
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
              {/* Data points */}
              {[
                {x: 0, y: 50}, {x: 16, y: 35}, {x: 33, y: 55}, {x: 50, y: 38}, 
                {x: 66, y: 45}, {x: 83, y: 15}, {x: 100, y: 20}
              ].map((p, i) => (
                <circle key={i} cx={`${p.x}%`} cy={`${p.y}%`} r="4" className="fill-[#10b981] stroke-background stroke-[2px]" />
              ))}
            </svg>
          </div>

          {/* X Axis Labels */}
          <div className="absolute bottom-0 left-8 right-4 flex justify-between text-[10px] text-muted-foreground mt-2">
            <span>May 19</span>
            <span>May 20</span>
            <span>May 21</span>
            <span>May 22</span>
            <span>May 23</span>
            <span>May 24</span>
            <span>May 25</span>
          </div>
        </div>
      </div>

      {/* Query Type Distribution (Donut) */}
      <div className="bg-[#12181f] border border-[#1e2329] rounded-xl p-5 flex flex-col min-h-[280px]">
        <span className="text-xs font-semibold text-foreground mb-6 block">Query Type Distribution</span>
        
        <div className="flex-1 flex items-center justify-center">
          <div className="relative w-32 h-32 flex-shrink-0">
            {/* SVG Donut */}
            <svg viewBox="0 0 100 100" className="w-full h-full transform -rotate-90">
              <circle cx="50" cy="50" r="40" fill="transparent" stroke="#1e2329" strokeWidth="16" />
              {/* General QA (Green) 45% */}
              <circle cx="50" cy="50" r="40" fill="transparent" stroke="#10b981" strokeWidth="16" strokeDasharray={`${45 * 2.51} 251`} strokeDashoffset="0" />
              {/* Technical (Blue) 25% */}
              <circle cx="50" cy="50" r="40" fill="transparent" stroke="#3b82f6" strokeWidth="16" strokeDasharray={`${25 * 2.51} 251`} strokeDashoffset={`-${45 * 2.51}`} />
              {/* Code Search (Purple) 15% */}
              <circle cx="50" cy="50" r="40" fill="transparent" stroke="#8b5cf6" strokeWidth="16" strokeDasharray={`${15 * 2.51} 251`} strokeDashoffset={`-${70 * 2.51}`} />
              {/* Doc Search (Orange) 15% (combining rest for mock) */}
              <circle cx="50" cy="50" r="40" fill="transparent" stroke="#f97316" strokeWidth="16" strokeDasharray={`${15 * 2.51} 251`} strokeDashoffset={`-${85 * 2.51}`} />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
              <span className="text-sm font-bold text-foreground">12,845</span>
              <span className="text-[10px] text-muted-foreground">Total</span>
            </div>
          </div>
          
          {/* Legend */}
          <div className="ml-6 flex flex-col space-y-3 w-full">
            {[
              { label: 'General QA', val: '45.2%', color: 'bg-[#10b981]' },
              { label: 'Technical', val: '24.7%', color: 'bg-[#3b82f6]' },
              { label: 'Code Search', val: '15.6%', color: 'bg-[#8b5cf6]' },
              { label: 'Document Search', val: '8.3%', color: 'bg-[#f97316]' },
              { label: 'Other', val: '6.2%', color: 'bg-[#9ca3af]' },
            ].map(item => (
              <div key={item.label} className="flex items-center justify-between text-[10px]">
                <div className="flex items-center space-x-2">
                  <div className={`w-2 h-2 rounded-full ${item.color}`} />
                  <span className="text-muted-foreground">{item.label}</span>
                </div>
                <span className="text-foreground">{item.val}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="w-full text-center mt-4">
          <span className="text-[10px] text-[#10b981] hover:text-[#059669] transition-colors cursor-pointer inline-flex items-center">
            View full breakdown <span className="ml-1">→</span>
          </span>
        </div>
      </div>

      {/* Response Time (Span 1 or 1.5 visually) */}
      <div className="lg:col-span-1 bg-[#12181f] border border-[#1e2329] rounded-xl p-5 flex flex-col h-[220px]">
        <ChartHeader title="Response Time (s)" controls={['Daily']} />
        <span className="text-[10px] text-muted-foreground -mt-3 mb-6 block">Average response time over time</span>
        
        <div className="flex-1 relative w-full h-full pt-2">
          {/* Y Axis Labels */}
          <div className="absolute left-0 top-0 bottom-6 flex flex-col justify-between text-[9px] text-muted-foreground">
            <span>2.5s</span>
            <span>2s</span>
            <span>1.5s</span>
            <span>1s</span>
            <span>0.5s</span>
            <span>0s</span>
          </div>
          
          <div className="absolute left-6 right-4 top-2 bottom-6">
            <div className="w-full h-full flex flex-col justify-between border-b border-[#30363d]">
              {[0,1,2,3,4].map(i => <div key={i} className="w-full h-[1px] bg-[#30363d]/30" />)}
            </div>
            <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="absolute inset-0 w-full h-full overflow-visible">
              <path 
                d="M 0 60 L 16 35 L 33 45 L 50 50 L 66 45 L 83 55 L 100 50" 
                fill="none" 
                stroke="#8b5cf6" 
                strokeWidth="2" 
                vectorEffect="non-scaling-stroke"
                className="drop-shadow-[0_4px_6px_rgba(139,92,246,0.5)]"
              />
              <path 
                d="M 0 60 L 16 35 L 33 45 L 50 50 L 66 45 L 83 55 L 100 50 L 100 100 L 0 100 Z" 
                fill="url(#grad-rt)" 
                vectorEffect="non-scaling-stroke"
                className="opacity-20"
              />
              <defs>
                <linearGradient id="grad-rt" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#8b5cf6" stopOpacity="1" />
                  <stop offset="100%" stopColor="#8b5cf6" stopOpacity="0" />
                </linearGradient>
              </defs>
              {[
                {x: 0, y: 60}, {x: 16, y: 35}, {x: 33, y: 45}, {x: 50, y: 50}, 
                {x: 66, y: 45}, {x: 83, y: 55}, {x: 100, y: 50}
              ].map((p, i) => (
                <circle key={i} cx={`${p.x}%`} cy={`${p.y}%`} r="3" className="fill-[#8b5cf6] stroke-background stroke-[1.5px]" />
              ))}
            </svg>
          </div>
          
          <div className="absolute bottom-0 left-6 right-4 flex justify-between text-[9px] text-muted-foreground mt-2">
             <span>May 19</span>
             <span>May 22</span>
             <span>May 25</span>
          </div>
        </div>
      </div>

      {/* Tokens Used (Span 2 visually in grid, but let's make it col-span-2) */}
      <div className="lg:col-span-2 bg-[#12181f] border border-[#1e2329] rounded-xl p-5 flex flex-col h-[220px]">
        <ChartHeader title="Tokens Used" controls={['Daily']} />
        <span className="text-[10px] text-muted-foreground -mt-3 mb-6 block">Tokens consumed over time</span>
        
        <div className="flex-1 relative w-full h-full pt-2">
          {/* Y Axis Labels */}
          <div className="absolute left-0 top-0 bottom-6 flex flex-col justify-between text-[9px] text-muted-foreground">
            <span>600K</span>
            <span>450K</span>
            <span>300K</span>
            <span>150K</span>
            <span>0</span>
          </div>
          
          <div className="absolute left-8 right-4 top-2 bottom-6">
            <div className="w-full h-full flex flex-col justify-between border-b border-[#30363d]">
              {[0,1,2,3].map(i => <div key={i} className="w-full h-[1px] bg-[#30363d]/30" />)}
            </div>
            <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="absolute inset-0 w-full h-full overflow-visible">
              <path 
                d="M 0 60 L 16 35 L 33 55 L 50 50 L 66 45 L 83 30 L 100 35" 
                fill="none" 
                stroke="#eab308" 
                strokeWidth="2" 
                vectorEffect="non-scaling-stroke"
                className="drop-shadow-[0_4px_6px_rgba(234,179,8,0.5)]"
              />
              <path 
                d="M 0 60 L 16 35 L 33 55 L 50 50 L 66 45 L 83 30 L 100 35 L 100 100 L 0 100 Z" 
                fill="url(#grad-tu)" 
                vectorEffect="non-scaling-stroke"
                className="opacity-20"
              />
              <defs>
                <linearGradient id="grad-tu" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#eab308" stopOpacity="1" />
                  <stop offset="100%" stopColor="#eab308" stopOpacity="0" />
                </linearGradient>
              </defs>
              {[
                {x: 0, y: 60}, {x: 16, y: 35}, {x: 33, y: 55}, {x: 50, y: 50}, 
                {x: 66, y: 45}, {x: 83, y: 30}, {x: 100, y: 35}
              ].map((p, i) => (
                <circle key={i} cx={`${p.x}%`} cy={`${p.y}%`} r="3" className="fill-[#eab308] stroke-background stroke-[1.5px]" />
              ))}
            </svg>
          </div>
          
          <div className="absolute bottom-0 left-8 right-4 flex justify-between text-[9px] text-muted-foreground mt-2">
            <span>May 19</span>
            <span>May 20</span>
            <span>May 21</span>
            <span>May 22</span>
            <span>May 23</span>
            <span>May 24</span>
            <span>May 25</span>
          </div>
        </div>
      </div>

    </div>
  );
}
