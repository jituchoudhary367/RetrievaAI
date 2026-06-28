"use client";

import React from 'react';
import { UploadCloud, FolderUp, Link } from 'lucide-react';

export function IngestionUploadArea() {
  return (
    <div className="flex items-center justify-between bg-[#12181f] border border-[#1e2329] rounded-xl p-8 border-dashed">
      
      {/* Drag & Drop Text */}
      <div className="flex items-center space-x-6">
        <div className="flex items-center justify-center w-16 h-16 rounded-2xl bg-[#10b981]/10 border border-[#10b981]/20 text-[#10b981]">
          <UploadCloud className="w-8 h-8" strokeWidth={1.5} />
        </div>
        <div className="flex flex-col space-y-1">
          <h3 className="text-base font-semibold text-foreground">Drag & drop files here or click to browse</h3>
          <p className="text-xs text-muted-foreground">Supports: PDF, DOCX, TXT, MD, HTML, CSV, JSON, Images</p>
          <p className="text-[10px] text-muted-foreground pt-1">Max file size: 200MB</p>
        </div>
      </div>

      <div className="text-sm font-semibold text-muted-foreground">OR</div>

      {/* Action Buttons */}
      <div className="flex flex-col space-y-3">
        <button className="flex items-center justify-center w-40 py-2.5 bg-[#1e2329] hover:bg-[#30363d] border border-[#30363d] rounded-md transition-colors text-xs font-medium text-foreground">
          <FolderUp className="w-4 h-4 mr-2 text-muted-foreground" />
          Select Files
        </button>
        <button className="flex items-center justify-center w-40 py-2.5 bg-[#1e2329] hover:bg-[#30363d] border border-[#30363d] rounded-md transition-colors text-xs font-medium text-foreground">
          <Link className="w-4 h-4 mr-2 text-muted-foreground" />
          Enter URL
        </button>
      </div>
      
    </div>
  );
}
