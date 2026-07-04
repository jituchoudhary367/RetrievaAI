"use client";

import React, { useRef, useState } from 'react';
import { UploadCloud, FolderUp, Link } from 'lucide-react';
import { ingestionApi } from '../../lib/api/ingest';

export function IngestionUploadArea({ onUploadSuccess }: { onUploadSuccess?: () => void }) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [isDragging, setIsDragging] = useState(false);

  const processFile = async (file: File) => {
    setUploading(true);
    try {
      await ingestionApi.submitJob(file);
      if (onUploadSuccess) onUploadSuccess();
    } catch (err: any) {
      console.error("Upload failed", err);
      if (err?.statusCode === 401 || err?.name === 'AuthError') {
        alert("Your session has expired. Please log in again.");
        window.location.href = '/login';
      } else {
        alert("Upload failed. See console.");
      }
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    processFile(e.target.files[0]);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      processFile(e.dataTransfer.files[0]);
    }
  };

  return (
    <div 
      className={`flex flex-col items-center justify-center bg-[#12181f] border rounded-xl p-8 border-dashed relative transition-colors cursor-pointer group space-y-4 ${
        isDragging ? 'border-[#10b981] bg-[#10b981]/5' : 'border-[#1e2329] hover:border-[#30363d] hover:bg-[#161b22]'
      }`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={() => fileInputRef.current?.click()}
    >
      <input type="file" ref={fileInputRef} onChange={handleFileChange} className="hidden" />
      {uploading && (
        <div className="absolute inset-0 bg-background/50 flex items-center justify-center rounded-xl z-10">
          <span className="text-sm font-medium">Uploading...</span>
        </div>
      )}
      
      {/* Drag & Drop Icon */}
      <div className="flex items-center justify-center w-16 h-16 rounded-2xl bg-[#10b981]/10 border border-[#10b981]/20 text-[#10b981]">
        <UploadCloud className="w-8 h-8" strokeWidth={1.5} />
      </div>
      
      {/* Drag & Drop Text */}
      <div className="flex flex-col items-center space-y-1 text-center">
        <h3 className="text-base font-semibold text-foreground">Drag & drop files here or click to browse</h3>
        <p className="text-xs text-muted-foreground">Supports: PDF, DOCX, TXT, MD, HTML, CSV, JSON, Images</p>
        <p className="text-[10px] text-muted-foreground pt-1">Max file size: 200MB</p>
      </div>

      <div className="text-sm font-semibold text-muted-foreground">OR</div>

      {/* Action Buttons */}
      <button 
        onClick={(e) => {
          e.stopPropagation();
          fileInputRef.current?.click();
        }}
        className="flex items-center justify-center w-40 py-2.5 bg-[#1e2329] hover:bg-[#30363d] border border-[#30363d] rounded-md transition-colors text-xs font-medium text-foreground">
        <FolderUp className="w-4 h-4 mr-2 text-muted-foreground" />
        Select Files
      </button>
      
    </div>
  );
}
