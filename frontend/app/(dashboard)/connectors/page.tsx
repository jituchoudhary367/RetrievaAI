"use client";

import React, { useEffect, useState } from 'react';
import { ConnectorCard } from './components/ConnectorCard';
import { Plus, Hexagon, Loader2, AlertCircle } from 'lucide-react';
import { getAuthToken } from '@/lib/auth/session';

interface ConnectorData {
  id: string;
  provider: string;
  display_name: string;
  status: string;
  auto_sync: boolean;
}

interface ConnectorHealth {
  connector_id: string;
  overall_status: string;
  synced_files: number;
  failed_files: number;
}

export default function ConnectorsPage() {
  const [connectors, setConnectors] = useState<ConnectorData[]>([]);
  const [healthMap, setHealthMap] = useState<Record<string, ConnectorHealth>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [isAdding, setIsAdding] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const token = getAuthToken();
      
      // Fetch connectors
      const connRes = await fetch('/api/connectors', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!connRes.ok) throw new Error('Failed to fetch connectors');
      const connData = await connRes.json();
      
      // Fetch health
      const healthRes = await fetch('/api/analytics/connector-health', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      let healthData = [];
      if (healthRes.ok) {
        healthData = await healthRes.json();
      }
      
      const map: Record<string, ConnectorHealth> = {};
      healthData.forEach((h: ConnectorHealth) => {
        // Just take the latest sample per connector
        if (!map[h.connector_id]) {
          map[h.connector_id] = h;
        }
      });
      
      setConnectors(connData);
      setHealthMap(map);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleAddConnector = async (provider: string) => {
    try {
      setIsAdding(true);
      const token = getAuthToken();
      const res = await fetch('/api/connectors', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}` 
        },
        body: JSON.stringify({ provider })
      });
      
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || 'Failed to create connector');
      }
      
      const data = await res.json();
      // Redirect to OAuth URL
      if (data.auth_url) {
        window.location.href = data.auth_url;
      } else {
        await fetchData();
      }
    } catch (err: any) {
      alert(err.message);
    } finally {
      setIsAdding(false);
    }
  };

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center bg-background text-foreground">
        <Loader2 className="w-8 h-8 animate-spin text-[#10b981]" />
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-background overflow-y-auto">
      <div className="p-8 max-w-6xl mx-auto w-full">
        
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-8 gap-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-100 flex items-center">
              <Hexagon className="w-8 h-8 mr-3 text-[#10b981]" />
              Connectors
            </h1>
            <p className="text-gray-400 mt-2 text-sm max-w-xl">
              Manage your enterprise integrations. Connect to external data sources to automatically ingest and index content into RetrievaAI.
            </p>
          </div>
          
          <div className="flex relative group">
            <button 
              className="flex items-center px-4 py-2 bg-[#10b981] hover:bg-[#059669] text-white rounded-md font-medium transition-colors shadow-sm"
              disabled={isAdding}
            >
              {isAdding ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Plus className="w-4 h-4 mr-2" />}
              Add Connector
            </button>
            {/* Simple dropdown on hover for demo */}
            <div className="absolute right-0 top-full mt-1 w-48 bg-[#1a212a] border border-[#30363d] rounded-md shadow-lg hidden group-hover:block z-10 overflow-hidden">
              <div className="p-2">
                <button 
                  onClick={() => handleAddConnector('google_drive')}
                  className="w-full text-left px-3 py-2 text-sm text-gray-200 hover:bg-[#30363d] hover:text-[#10b981] rounded-sm transition-colors"
                >
                  Google Drive
                </button>
                {/* Add more providers here later */}
              </div>
            </div>
          </div>
        </div>

        {error && (
          <div className="mb-8 p-4 bg-red-500/10 border border-red-500/30 rounded-md flex items-start text-red-400">
            <AlertCircle className="w-5 h-5 mr-3 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="font-medium">Error loading connectors</h3>
              <p className="text-sm opacity-90 mt-1">{error}</p>
            </div>
          </div>
        )}

        {connectors.length === 0 && !error ? (
          <div className="flex flex-col items-center justify-center p-12 bg-[#121820] border border-[#30363d] border-dashed rounded-xl mt-4">
            <Hexagon className="w-16 h-16 text-gray-600 mb-4" />
            <h2 className="text-xl font-semibold text-gray-200 mb-2">No Connectors Active</h2>
            <p className="text-gray-400 text-center max-w-md mb-6">
              You haven't connected any external data sources yet. Add a connector to start importing your enterprise knowledge automatically.
            </p>
            <button 
              onClick={() => handleAddConnector('google_drive')}
              className="px-6 py-2.5 bg-[#1a212a] hover:bg-[#30363d] text-[#10b981] border border-[#30363d] rounded-md font-medium transition-colors flex items-center"
            >
              <Plus className="w-4 h-4 mr-2" /> Connect Google Drive
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {connectors.map(c => (
              <ConnectorCard 
                key={c.id} 
                id={c.id}
                provider={c.provider}
                displayName={c.display_name}
                status={c.status}
                autoSync={c.auto_sync}
                health={healthMap[c.id]}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
