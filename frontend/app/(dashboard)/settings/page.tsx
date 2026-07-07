"use client";

import React, { useState, useEffect, useCallback } from 'react';
import { TopBar } from '@/components/layout/TopBar';
import RequireAuth from '@/components/auth/RequireAuth';
import { settingsApi, ApiKeyOut, SessionOut, AuditLogEntry } from '@/lib/api/settings';
import { apiFetch } from '@/lib/api/client';
import { postRequestPasswordReset } from '@/lib/api/auth';
import { useHealthPolling } from '@/lib/hooks/useHealthPolling';
import { getUserInfo, getRoles } from '@/lib/auth/session';
import { Key, Shield, Trash2, Plus, Copy, Eye, EyeOff, LogOut, RefreshCw, Clock } from 'lucide-react';
import ConnectorsPanel from '@/components/connectors/ConnectorsPanel';


function SectionCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-[#12181f] border border-[#1e2329] rounded-xl p-5 flex flex-col space-y-4">
      <h3 className="text-xs font-semibold text-foreground">{title}</h3>
      {children}
    </div>
  );
}

function Row({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between text-xs">
      <span className="text-muted-foreground">{label}</span>
      <span className="text-foreground">{value}</span>
    </div>
  );
}

export default function SettingsPage() {
  const [apiKeys, setApiKeys] = useState<ApiKeyOut[]>([]);
  const [sessions, setSessions] = useState<SessionOut[]>([]);
  const [auditLog, setAuditLog] = useState<AuditLogEntry[]>([]);
  const [newKeyName, setNewKeyName] = useState('');
  const [createdKey, setCreatedKey] = useState<string | null>(null);
  const [showKey, setShowKey] = useState(false);
  const [isLoadingKeys, setIsLoadingKeys] = useState(true);
  const [toastMsg, setToastMsg] = useState<string | null>(null);

  const [groqKey, setGroqKey] = useState('');
  const [showGroqKey, setShowGroqKey] = useState(false);
  const [tavilyKey, setTavilyKey] = useState('');
  const [showTavilyKey, setShowTavilyKey] = useState(false);
  const [serperKey, setSerperKey] = useState('');
  const [showSerperKey, setShowSerperKey] = useState(false);
  const [isSavingIntegrations, setIsSavingIntegrations] = useState(false);
  const [isRequestingReset, setIsRequestingReset] = useState(false);

  const { health } = useHealthPolling(30000);
  const userInfo = getUserInfo();
  const roles = getRoles();
  const isAdmin = roles.includes('TENANT_ADMIN');

  const showToast = (msg: string) => {
    setToastMsg(msg);
    setTimeout(() => setToastMsg(null), 3000);
  };

  const fetchAll = useCallback(async () => {
    setIsLoadingKeys(true);
    try {
      const [keys, sess, log, integrations] = await Promise.allSettled([
        settingsApi.listApiKeys(),
        settingsApi.listSessions(),
        settingsApi.getAuditLog(5),
        settingsApi.getCategory('integrations')
      ]);
      if (keys.status === 'fulfilled') setApiKeys(keys.value);
      if (sess.status === 'fulfilled') setSessions(sess.value);
      if (log.status === 'fulfilled') setAuditLog(log.value);
      if (integrations.status === 'fulfilled') {
        setGroqKey(integrations.value.GROQ_API_KEY || integrations.value.OPENAI_API_KEY || '');
        setTavilyKey(integrations.value.TAVILY_API_KEY || '');
        setSerperKey(integrations.value.SERPER_API_KEY || '');
      }
    } finally {
      setIsLoadingKeys(false);
    }
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  const handleSaveIntegrations = async () => {
    setIsSavingIntegrations(true);
    try {
      await settingsApi.updateCategory('integrations', {
        GROQ_API_KEY: groqKey.trim(),
        TAVILY_API_KEY: tavilyKey.trim()
      });
      showToast('Integrations saved');
    } catch {
      showToast('Failed to save integrations');
    } finally {
      setIsSavingIntegrations(false);
    }
  };

  const handleSaveWebSearch = async () => {
    setIsSavingIntegrations(true);
    try {
      await apiFetch('/api/settings/serper', {
        method: 'POST',
        body: JSON.stringify({ serper_api_key: serperKey.trim() })
      });
      showToast('Web Search integration saved');
    } catch {
      showToast('Failed to save Web Search integration');
    } finally {
      setIsSavingIntegrations(false);
    }
  };

  const handleRequestPasswordReset = async () => {
    if (!userInfo?.email) return;
    setIsRequestingReset(true);
    try {
      await postRequestPasswordReset({ email: userInfo.email });
      showToast('Password reset link sent to email');
    } catch {
      showToast('Failed to request password reset');
    } finally {
      setIsRequestingReset(false);
    }
  };

  const handleCreateKey = async () => {
    if (!newKeyName.trim()) return;
    try {
      const result = await settingsApi.createApiKey(newKeyName.trim());
      setCreatedKey(result.key);
      setNewKeyName('');
      setApiKeys(prev => [...prev, { id: result.id, name: result.name, prefix: result.key.slice(0, 10), lastUsedAt: null, createdAt: new Date().toISOString() }]);
      showToast('API key created');
    } catch {
      showToast('Failed to create API key');
    }
  };

  const handleRevokeKey = async (keyId: string) => {
    try {
      await settingsApi.revokeApiKey(keyId);
      setApiKeys(prev => prev.filter(k => k.id !== keyId));
      showToast('API key revoked');
    } catch {
      showToast('Failed to revoke key');
    }
  };

  const handleRevokeSession = async (sessionId: string) => {
    try {
      await settingsApi.revokeSession(sessionId);
      setSessions(prev => prev.filter(s => s.id !== sessionId));
      showToast('Session revoked');
    } catch {
      showToast('Failed to revoke session');
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text).then(() => showToast('Copied!'));
  };

  const formatDate = (iso: string) => {
    try { return new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' }); }
    catch { return iso; }
  };

  const getComponentDotColor = (status: string) => {
    if (status === 'healthy') return 'bg-[#10b981]';
    if (status === 'degraded') return 'bg-yellow-500';
    return 'bg-red-500';
  };

  return (
    <RequireAuth>
      <div className="flex flex-col h-full bg-background relative overflow-hidden">
        <TopBar title="Settings" />

        {/* Toast */}
        {toastMsg && (
          <div className="fixed bottom-6 right-6 z-50 bg-[#10b981] text-white text-xs px-4 py-2 rounded-lg shadow-lg">
            {toastMsg}
          </div>
        )}

        <div className="flex flex-1 overflow-hidden">
          {/* Left — Main Settings */}
          <div className="flex-1 flex flex-col min-w-0 border-r border-border bg-background p-6 overflow-y-auto space-y-6">
            
            <div>
              <h2 className="text-lg font-bold text-foreground">Settings</h2>
              <p className="text-xs text-muted-foreground mt-1">Manage your account, API keys, and system configuration</p>
            </div>

            {/* Account Information */}
            <SectionCard title="Account Information">
              <Row label="Name" value={userInfo?.name || '—'} />
              <Row label="Email" value={userInfo?.email || '—'} />
              <Row label="Role" value={
                <span className="px-2 py-0.5 rounded text-[9px] bg-[#10b981]/10 text-[#10b981] border border-[#10b981]/20">
                  {roles.join(', ') || 'VIEWER'}
                </span>
              } />
            </SectionCard>

            {/* Data Connectors (Google Drive, etc.) */}
            <SectionCard title="Data Connectors">
              <ConnectorsPanel />
            </SectionCard>

            {/* Provider Integrations */}
            <SectionCard title="Provider Integrations">
              <div className="space-y-4">
                <div className="flex flex-col space-y-1">
                  <label className="text-xs text-muted-foreground">Groq API Key</label>
                  <div className="relative flex items-center">
                    <input
                      type={showGroqKey ? "text" : "password"}
                      value={groqKey}
                      onChange={e => setGroqKey(e.target.value)}
                      placeholder="gsk-..."
                      className="w-full bg-[#161b22] border border-[#30363d] rounded-md pl-3 pr-10 py-1.5 text-xs text-foreground placeholder-muted-foreground focus:outline-none focus:border-[#4b5563] transition-colors"
                    />
                    <button 
                      onClick={() => setShowGroqKey(!showGroqKey)}
                      className="absolute right-3 text-muted-foreground hover:text-foreground"
                    >
                      {showGroqKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>
                <button
                  onClick={handleSaveIntegrations}
                  disabled={isSavingIntegrations}
                  className="px-4 py-1.5 bg-[#10b981] hover:bg-[#059669] text-white text-xs rounded-md transition-colors disabled:opacity-50"
                >
                  {isSavingIntegrations ? 'Saving...' : 'Save Integrations'}
                </button>
              </div>
            </SectionCard>

            {/* Web Search Integration */}
            <SectionCard title="Web Search Integration">
              <div className="space-y-4">
                <div className="flex flex-col space-y-1">
                  <label className="text-xs text-muted-foreground">Serper API Key (Real-time Google Search)</label>
                  <div className="relative flex items-center">
                    <input
                      type={showSerperKey ? "text" : "password"}
                      value={serperKey}
                      onChange={e => setSerperKey(e.target.value)}
                      placeholder="Enter Serper API Key..."
                      className="w-full bg-[#161b22] border border-[#30363d] rounded-md pl-3 pr-10 py-1.5 text-xs text-foreground placeholder-muted-foreground focus:outline-none focus:border-[#4b5563] transition-colors"
                    />
                    <button 
                      onClick={() => setShowSerperKey(!showSerperKey)}
                      className="absolute right-3 text-muted-foreground hover:text-foreground"
                    >
                      {showSerperKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>
                <button
                  onClick={handleSaveWebSearch}
                  disabled={isSavingIntegrations || !serperKey.trim()}
                  className="px-4 py-1.5 bg-[#10b981] hover:bg-[#059669] text-white text-xs rounded-md transition-colors disabled:opacity-50"
                >
                  Save Web Search
                </button>
              </div>
            </SectionCard>

            {/* API Keys */}
            <SectionCard title="API Keys">
              {/* Created key reveal */}
              {createdKey && (
                <div className="bg-[#10b981]/10 border border-[#10b981]/20 rounded-lg p-3 text-xs space-y-2">
                  <p className="text-[#10b981] font-medium">New API key created — copy it now, it won't be shown again.</p>
                  <div className="flex items-center space-x-2">
                    <code className="flex-1 bg-background rounded px-2 py-1 text-[10px] font-mono text-foreground break-all">
                      {showKey ? createdKey : createdKey.slice(0, 12) + '••••••••••••••••••'}
                    </code>
                    <button onClick={() => setShowKey(v => !v)} className="text-muted-foreground hover:text-foreground">
                      {showKey ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                    </button>
                    <button onClick={() => copyToClipboard(createdKey)} className="text-muted-foreground hover:text-[#10b981]">
                      <Copy className="w-3.5 h-3.5" />
                    </button>
                  </div>
                  <button onClick={() => setCreatedKey(null)} className="text-[10px] text-muted-foreground hover:text-foreground">Dismiss</button>
                </div>
              )}

              {/* Create new key */}
              <div className="flex items-center space-x-2">
                <input
                  type="text"
                  placeholder="Key name (e.g. production-app)"
                  value={newKeyName}
                  onChange={e => setNewKeyName(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && handleCreateKey()}
                  className="flex-1 bg-[#161b22] border border-[#30363d] rounded-md px-3 py-1.5 text-xs text-foreground placeholder-muted-foreground focus:outline-none focus:border-[#4b5563] transition-colors"
                />
                <button
                  onClick={handleCreateKey}
                  className="flex items-center space-x-1 px-3 py-1.5 bg-[#10b981] hover:bg-[#059669] text-white text-xs rounded-md transition-colors"
                >
                  <Plus className="w-3 h-3" />
                  <span>Generate</span>
                </button>
              </div>

              {/* Key list */}
              {isLoadingKeys ? (
                <p className="text-xs text-muted-foreground">Loading keys...</p>
              ) : apiKeys.length === 0 ? (
                <p className="text-xs text-muted-foreground">No API keys yet</p>
              ) : (
                <div className="space-y-2">
                  {apiKeys.map(k => (
                    <div key={k.id} className="flex items-center justify-between p-3 bg-[#161b22] border border-[#30363d] rounded-lg text-xs">
                      <div className="flex items-center space-x-3">
                        <Key className="w-3.5 h-3.5 text-muted-foreground" />
                        <div>
                          <p className="text-foreground font-medium">{k.name}</p>
                          <p className="text-[10px] text-muted-foreground font-mono">{k.prefix}••••••••</p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-3">
                        <span className="text-[10px] text-muted-foreground">{k.lastUsedAt ? formatDate(k.lastUsedAt) : 'Never used'}</span>
                        <button
                          onClick={() => handleRevokeKey(k.id)}
                          className="text-red-500 hover:text-red-400 transition-colors"
                          title="Revoke"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </SectionCard>

            {/* Active Sessions */}
            <SectionCard title="Active Sessions">
              {sessions.length === 0 ? (
                <p className="text-xs text-muted-foreground">No active sessions</p>
              ) : (
                sessions.map(s => (
                  <div key={s.id} className="flex items-center justify-between p-3 bg-[#161b22] border border-[#30363d] rounded-lg text-xs">
                    <div className="flex items-center space-x-3">
                      <Shield className="w-3.5 h-3.5 text-muted-foreground" />
                      <div>
                        <p className="text-foreground font-medium">{s.ipAddress || 'Unknown IP'}</p>
                        <p className="text-[10px] text-muted-foreground truncate max-w-[200px]">{s.userAgent || 'Unknown browser'}</p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-3">
                      <span className="text-[10px] text-muted-foreground">{formatDate(s.lastSeenAt)}</span>
                      <button
                        onClick={() => handleRevokeSession(s.id)}
                        className="text-red-500 hover:text-red-400 transition-colors"
                        title="Revoke session"
                      >
                        <LogOut className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                ))
              )}
            </SectionCard>

          </div>

          {/* Right Panel */}
          <div className="w-80 flex-shrink-0 flex flex-col bg-muted/10 overflow-y-auto hidden lg:flex p-6 space-y-6">
            
            {/* Integrations — from health check */}
            <SectionCard title="Integrations">
              {health?.components && health.components.length > 0 ? (
                health.components.map(comp => (
                  <div key={comp.name} className="flex items-center justify-between text-xs">
                    <div className="flex items-center space-x-2">
                      <div className={`w-1.5 h-1.5 rounded-full ${getComponentDotColor(comp.status)}`} />
                      <span className="text-muted-foreground capitalize">{comp.name}</span>
                    </div>
                    <span className={
                      comp.status === 'healthy' ? 'text-[#10b981]' :
                      comp.status === 'degraded' ? 'text-yellow-500' : 'text-red-500'
                    }>
                      {comp.status === 'healthy' ? 'Connected' : comp.status === 'degraded' ? 'Degraded' : 'Error'}
                    </span>
                  </div>
                ))
              ) : (
                <p className="text-xs text-muted-foreground">Checking integrations...</p>
              )}
            </SectionCard>

            {/* Recent Activity — from audit log */}
            <SectionCard title="Recent Activity">
              {auditLog.length === 0 ? (
                <p className="text-xs text-muted-foreground">No recent activity</p>
              ) : (
                auditLog.map(entry => (
                  <div key={entry.id} className="flex items-start space-x-2 text-xs">
                    <Clock className="w-3 h-3 text-muted-foreground mt-0.5 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-foreground text-[10px]">{entry.action.replace(/\./g, ' › ')}</p>
                      <p className="text-[9px] text-muted-foreground">{formatDate(entry.createdAt)}</p>
                    </div>
                  </div>
                ))
              )}
            </SectionCard>

            {/* Security Info */}
            <SectionCard title="Security">
              <p className="text-[10px] text-muted-foreground leading-relaxed mb-3">
                To change your password securely, you can request a password reset link to be sent to your email.
              </p>
              <button
                onClick={handleRequestPasswordReset}
                disabled={isRequestingReset}
                className="w-full py-1.5 bg-[#1e2329] hover:bg-[#30363d] border border-[#30363d] text-foreground text-xs rounded-md transition-colors disabled:opacity-50"
              >
                {isRequestingReset ? 'Requesting...' : 'Request Password Reset'}
              </button>
            </SectionCard>

          </div>
        </div>
      </div>
    </RequireAuth>
  );
}
