"use client";

import React from 'react';
import { AlertTriangle, Download, RefreshCw, Trash2 } from 'lucide-react';

export function DangerZone() {
  return (
    <div className="bg-[#12181f] border border-red-500/20 rounded-xl flex flex-col md:flex-row items-start md:items-center justify-between p-6 gap-6 relative overflow-hidden">

      {/* Subtle red glow background */}
      <div className="absolute top-0 left-0 w-1/3 h-full bg-gradient-to-r from-red-500/5 to-transparent pointer-events-none" />

      <div className="flex items-start space-x-4 relative z-10">
        <div className="w-10 h-10 rounded-lg bg-red-500/10 flex items-center justify-center flex-shrink-0 border border-red-500/20">
          <AlertTriangle className="w-5 h-5 text-red-500" strokeWidth={1.5} />
        </div>
        <div className="flex flex-col">
          <h3 className="text-sm font-semibold text-red-500">Danger Zone</h3>
          <p className="text-[11px] text-muted-foreground mt-0.5 max-w-md leading-relaxed">
            Irreversible and destructive actions.<br />
            <span className="text-red-400">These actions cannot be undone. Please be certain before proceeding.</span>
          </p>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-3 relative z-10 w-full md:w-auto">
        <button className="flex-1 md:flex-none flex items-center justify-center space-x-2 px-4 py-2 rounded-md border border-[#30363d] bg-transparent text-muted-foreground hover:text-foreground hover:bg-[#21262d] hover:border-[#4b5563] transition-colors text-xs font-medium">
          <Download className="w-3.5 h-3.5" />
          <span>Export System Data</span>
        </button>
        <button className="flex-1 md:flex-none flex items-center justify-center space-x-2 px-4 py-2 rounded-md border border-yellow-500/30 bg-yellow-500/5 text-yellow-500 hover:bg-yellow-500/10 hover:border-yellow-500/50 transition-colors text-xs font-medium">
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Reset System</span>
        </button>
        <button className="flex-1 md:flex-none flex items-center justify-center space-x-2 px-4 py-2 rounded-md border border-red-500/30 bg-red-500/5 text-red-500 hover:bg-red-500/10 hover:border-red-500/50 transition-colors text-xs font-medium">
          <Trash2 className="w-3.5 h-3.5" />
          <span>Delete System</span>
        </button>
      </div>

    </div>
  );
}
