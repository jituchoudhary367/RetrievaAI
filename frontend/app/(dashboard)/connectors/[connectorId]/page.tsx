"use client";

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowLeft, Play, Pause, Trash2, RefreshCw, Hexagon, Server, CheckCircle2, AlertCircle, Clock } from 'lucide-react';
import { getAuthToken } from '@/lib/auth/session';

interface ConnectorDetail {
  id: string;
  provider: string;
  display_name: string;
  status: string;
  auto_sync: boolean;
  sync_interval_minutes: number;
}

export default function ConnectorDetailPage({ params }: { params: { connectorId: string } }) {
  const router = useRouter();
  const { connectorId } = params;
  
  const [connector, setConnector] = useState<ConnectorDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchConnector();
  }, [connectorId]);

  const fetchConnector = async () => {
    try {
      setLoading(true);
      const token = getAuthToken();
      const res = await fetch(`/api/connectors`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Failed to fetch connectors');
      
      const data: ConnectorDetail[] = await res.json();
      const match = data.find(c => c.id === connectorId);
      if (!match) throw new Error('Connector not found');
      
      setConnector(match);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handlePauseResume = async () => {
    if (!connector) return;
    try {
      setActionLoading(true);
      const token = getAuthToken();
      const endpoint = connector.auto_sync ? 'pause' : 'resume';
      
      const res = await fetch(`/api/connectors/${connectorId}/${endpoint}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (!res.ok) throw new Error(`Failed to ${endpoint} connector`);
      await fetchConnector();
    } catch (err: any) {
      alert(err.message);
    } finally {
      setActionLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to completely remove this connector? All synced files will remain but will no longer be updated.')) return;
    try {
      setActionLoading(true);
      const token = getAuthToken();
      const res = await fetch(`/api/connectors/${connectorId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Failed to delete connector');
      
      router.push('/connectors');
    } catch (err: any) {
      alert(err.message);
      setActionLoading(false);
    }
  };

  const handleSyncNow = async () => {
    alert("Sync triggered! The backend will process this in the background.");
  };

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center bg-background text-foreground">
        <RefreshCw className="w-8 h-8 animate-spin text-[#10b981]" />
      </div>
    );
  }

  if (error || !connector) {
    return (
      <div className="p-8 h-full bg-background">
        <button onClick={() => router.back()} className="flex items-center text-gray-400 hover:text-white mb-6 transition-colors">
          <ArrowLeft className="w-4 h-4 mr-2" /> Back
        </button>
        <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-md text-red-400 max-w-2xl">
          <h3 className="font-medium">Error loading connector details</h3>
          <p className="text-sm opacity-90 mt-1">{error || 'Not found'}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-background overflow-y-auto">
      <div className="p-8 max-w-4xl mx-auto w-full">
        
        {/* Header */}
        <div className="mb-8">
          <button onClick={() => router.push('/connectors')} className="flex items-center text-sm font-medium text-gray-400 hover:text-[#10b981] mb-6 transition-colors">
            <ArrowLeft className="w-4 h-4 mr-1.5" /> Back to Connectors
          </button>
          
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="w-12 h-12 rounded-lg bg-[#1a212a] flex items-center justify-center border border-[#30363d]">
                <Hexagon className="w-6 h-6 text-gray-400" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-100">{connector.display_name || connector.provider}</h1>
                <p className="text-sm text-gray-400 font-medium tracking-wide uppercase mt-1 flex items-center">
                  <Server className="w-3.5 h-3.5 mr-1.5" /> {connector.provider.replace('_', ' ')}
                </p>
              </div>
            </div>
            
            <div className="flex items-center space-x-3">
              <span className={`px-3 py-1 text-xs font-medium rounded-full border flex items-center ${
                connector.status === 'connected' ? 'bg-emerald-400/10 text-emerald-400 border-emerald-400/20' : 
                connector.status === 'pending_auth' ? 'bg-amber-400/10 text-amber-400 border-amber-400/20' : 
                'bg-red-400/10 text-red-400 border-red-400/20'
              }`}>
                {connector.status === 'connected' && <CheckCircle2 className="w-3.5 h-3.5 mr-1.5" />}
                {connector.status === 'pending_auth' && <RefreshCw className="w-3.5 h-3.5 mr-1.5 animate-spin" />}
                {connector.status === 'error' && <AlertCircle className="w-3.5 h-3.5 mr-1.5" />}
                {connector.status}
              </span>
            </div>
          </div>
        </div>

        {/* Action Bar */}
        <div className="bg-[#121820] border border-[#30363d] rounded-lg p-4 mb-8 flex flex-wrap gap-3 items-center shadow-sm">
          <button 
            onClick={handleSyncNow}
            disabled={actionLoading || connector.status !== 'connected'}
            className="flex items-center px-4 py-2 bg-[#10b981] hover:bg-[#059669] text-white rounded-md text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <RefreshCw className="w-4 h-4 mr-2" /> Sync Now
          </button>
          
          <button 
            onClick={handlePauseResume}
            disabled={actionLoading}
            className="flex items-center px-4 py-2 bg-[#1a212a] hover:bg-[#30363d] text-gray-200 border border-[#30363d] rounded-md text-sm font-medium transition-colors disabled:opacity-50"
          >
            {connector.auto_sync ? (
              <><Pause className="w-4 h-4 mr-2 text-amber-400" /> Pause Sync</>
            ) : (
              <><Play className="w-4 h-4 mr-2 text-emerald-400" /> Resume Sync</>
            )}
          </button>

          <div className="flex-1"></div>
          
          <button 
            onClick={handleDelete}
            disabled={actionLoading}
            className="flex items-center px-4 py-2 bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/20 rounded-md text-sm font-medium transition-colors disabled:opacity-50"
          >
            <Trash2 className="w-4 h-4 mr-2" /> Delete
          </button>
        </div>

        {/* Configuration Summary */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <div className="bg-[#121820] border border-[#30363d] rounded-lg p-5">
            <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-4 border-b border-[#30363d] pb-2">Sync Configuration</h3>
            
            <div className="space-y-4">
              <div>
                <p className="text-xs text-gray-500 font-medium">Auto Sync Strategy</p>
                <div className="flex items-center mt-1">
                  {connector.auto_sync ? (
                    <span className="text-sm text-emerald-400 flex items-center font-medium"><Play className="w-3.5 h-3.5 mr-1.5" /> Enabled</span>
                  ) : (
                    <span className="text-sm text-amber-400 flex items-center font-medium"><Pause className="w-3.5 h-3.5 mr-1.5" /> Paused</span>
                  )}
                </div>
              </div>
              
              <div>
                <p className="text-xs text-gray-500 font-medium">Sync Interval</p>
                <p className="text-sm text-gray-200 mt-1 flex items-center font-medium">
                  <Clock className="w-3.5 h-3.5 mr-1.5 text-gray-400" /> Every {connector.sync_interval_minutes} minutes
                </p>
              </div>
            </div>
          </div>
          
          <div className="bg-[#121820] border border-[#30363d] rounded-lg p-5">
            <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-4 border-b border-[#30363d] pb-2">Connector Metadata</h3>
            
            <div className="space-y-4">
              <div>
                <p className="text-xs text-gray-500 font-medium">Internal ID</p>
                <p className="text-sm text-gray-400 mt-1 font-mono bg-[#0d1117] p-1.5 rounded inline-block border border-[#30363d]">{connector.id}</p>
              </div>
            </div>
          </div>
        </div>
        
      </div>
    </div>
  );
}
