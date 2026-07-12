"use client";

import React from 'react';
import Link from 'next/link';
import { Settings, RefreshCw, AlertCircle, CheckCircle2, PauseCircle } from 'lucide-react';

interface ConnectorCardProps {
  id: string;
  provider: string;
  displayName: string;
  status: string;
  autoSync: boolean;
  health?: {
    overall_status: string;
    synced_files: number;
    failed_files: number;
  };
}

export function ConnectorCard({ id, provider, displayName, status, autoSync, health }: ConnectorCardProps) {
  const isHealthy = health?.overall_status === 'healthy';
  const hasErrors = status === 'error' || health?.overall_status === 'degraded' || health?.overall_status === 'unhealthy';

  return (
    <div className="bg-[#121820] border border-[#30363d] rounded-lg overflow-hidden flex flex-col transition-all hover:border-[#10b981]/50 shadow-sm">
      <div className="p-5 flex-1">
        <div className="flex justify-between items-start mb-4">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-md bg-[#1a212a] flex items-center justify-center border border-[#30363d]">
              {/* Fallback provider icon */}
              <span className="font-bold text-gray-300 text-sm">
                {provider === 'google_drive' ? 'GD' : provider.substring(0, 2).toUpperCase()}
              </span>
            </div>
            <div>
              <h3 className="font-semibold text-gray-200 text-base">{displayName || provider}</h3>
              <p className="text-xs text-gray-400 capitalize">{provider.replace('_', ' ')}</p>
            </div>
          </div>
          <div className="flex items-center">
            {status === 'connected' && !hasErrors && (
              <span className="flex items-center text-xs font-medium text-emerald-400 bg-emerald-400/10 px-2 py-1 rounded-full border border-emerald-400/20">
                <CheckCircle2 className="w-3 h-3 mr-1" /> Connected
              </span>
            )}
            {status === 'pending_auth' && (
              <span className="flex items-center text-xs font-medium text-amber-400 bg-amber-400/10 px-2 py-1 rounded-full border border-amber-400/20">
                <RefreshCw className="w-3 h-3 mr-1 animate-spin" /> Pending Auth
              </span>
            )}
            {hasErrors && (
              <span className="flex items-center text-xs font-medium text-red-400 bg-red-400/10 px-2 py-1 rounded-full border border-red-400/20">
                <AlertCircle className="w-3 h-3 mr-1" /> Error
              </span>
            )}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4 mt-6">
          <div className="bg-[#0d1117] p-3 rounded-md border border-[#30363d]">
            <p className="text-xs text-gray-500 mb-1 font-medium uppercase tracking-wider">Auto Sync</p>
            <div className="flex items-center text-sm">
              {autoSync ? (
                <span className="text-emerald-400 flex items-center"><RefreshCw className="w-3 h-3 mr-1.5" /> Active</span>
              ) : (
                <span className="text-amber-400 flex items-center"><PauseCircle className="w-3 h-3 mr-1.5" /> Paused</span>
              )}
            </div>
          </div>
          
          <div className="bg-[#0d1117] p-3 rounded-md border border-[#30363d]">
            <p className="text-xs text-gray-500 mb-1 font-medium uppercase tracking-wider">Files Indexed</p>
            <p className="text-sm font-semibold text-gray-300">
              {health ? health.synced_files : 0}
            </p>
          </div>
        </div>
        
        {health?.failed_files > 0 && (
          <div className="mt-3 text-xs text-red-400 flex items-center bg-red-400/5 px-2 py-1.5 rounded">
            <AlertCircle className="w-3.5 h-3.5 mr-1.5 flex-shrink-0" />
            <span>{health.failed_files} file{health.failed_files !== 1 ? 's' : ''} failed to sync</span>
          </div>
        )}
      </div>
      
      <div className="bg-[#0d1117] px-5 py-3 border-t border-[#30363d] flex justify-end">
        <Link 
          href={`/connectors/${id}`}
          className="flex items-center text-sm font-medium text-[#10b981] hover:text-[#34d399] transition-colors"
        >
          <Settings className="w-4 h-4 mr-1.5" />
          Manage
        </Link>
      </div>
    </div>
  );
}
