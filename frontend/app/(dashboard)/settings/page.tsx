"use client";

import React, { useState, useEffect, useCallback } from 'react';
import { TopBar } from '@/components/layout/TopBar';
import RequireAuth from '@/components/auth/RequireAuth';
import { settingsApi, ApiKeyOut, SessionOut, AuditLogEntry } from '@/lib/api/settings';
import { apiFetch } from '@/lib/api/client';
import { postRequestPasswordReset } from '@/lib/api/auth';
import { getUserInfo, getRoles } from '@/lib/auth/session';
import {
  Key, Shield, Trash2, Plus, Copy, Eye, EyeOff, LogOut, Clock, User
} from 'lucide-react';
import ConnectorsPanel from '@/components/connectors/ConnectorsPanel';

// Control Center components (new — additive layer)
import { ControlCenterLayout, CCTab } from '@/components/control-center/ControlCenterLayout';
import { LLMProvidersPanel } from '@/components/control-center/LLMProvidersPanel';
import { ModelHubPanel } from '@/components/control-center/ModelHubPanel';
import { EmbeddingProvidersPanel, SearchProvidersPanel } from '@/components/control-center/EmbeddingSearchPanels';
import { RuntimeConfigPanel } from '@/components/control-center/RuntimeConfigPanel';
import { HealthSidebar, UsageSidebar } from '@/components/control-center/HealthUsageSidebar';


// ── Preserved helpers (unchanged) ─────────────────────────────────────────────

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

// ── Legacy panels (preserved exactly) ─────────────────────────────────────────

function AccountPanel({ userInfo, roles, onReset, isResetting }: any) {
  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-base font-bold text-white">Account</h2>
        <p className="text-xs text-[#4a5568] mt-0.5">Your profile and security settings.</p>
      </div>
      <SectionCard title="Account Information">
        <Row label="Name" value={userInfo?.name || '—'} />
        <Row label="Email" value={userInfo?.email || '—'} />
        <Row label="Role" value={
          <span className="px-2 py-0.5 rounded text-[9px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            {roles.join(', ') || 'VIEWER'}
          </span>
        } />
      </SectionCard>
      <SectionCard title="Security">
        <p className="text-[10px] text-muted-foreground leading-relaxed">
          To change your password, request a reset link to your email address.
        </p>
        <button
          onClick={onReset}
          disabled={isResetting}
          className="w-full py-2 bg-[#1e2329] hover:bg-[#30363d] border border-[#30363d] text-white text-xs rounded-lg transition-colors disabled:opacity-50"
        >
          {isResetting ? 'Requesting…' : 'Request Password Reset'}
        </button>
      </SectionCard>
    </div>
  );
}

function ApiKeysPanel({ apiKeys, newKeyName, createdKey, showKey, isLoading, onCreateKey, onRevokeKey, onNameChange, onShowToggle, onCopy, onDismiss }: any) {
  const formatDate = (iso: string) => {
    try { return new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' }); }
    catch { return iso; }
  };
  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-base font-bold text-white">API Keys</h2>
        <p className="text-xs text-[#4a5568] mt-0.5">Manage programmatic access keys for your workspace.</p>
      </div>
      <SectionCard title="API Keys">
        {createdKey && (
          <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-lg p-3 text-xs space-y-2">
            <p className="text-emerald-400 font-medium">New API key created — copy it now, it won't be shown again.</p>
            <div className="flex items-center space-x-2">
              <code className="flex-1 bg-background rounded px-2 py-1 text-[10px] font-mono text-foreground break-all">
                {showKey ? createdKey : createdKey.slice(0, 12) + '••••••••••••••••••'}
              </code>
              <button onClick={onShowToggle} className="text-muted-foreground hover:text-foreground">
                {showKey ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
              </button>
              <button onClick={() => onCopy(createdKey)} className="text-muted-foreground hover:text-emerald-400">
                <Copy className="w-3.5 h-3.5" />
              </button>
            </div>
            <button onClick={onDismiss} className="text-[10px] text-muted-foreground hover:text-foreground">Dismiss</button>
          </div>
        )}
        <div className="flex items-center space-x-2">
          <input
            type="text"
            placeholder="Key name (e.g. production-app)"
            value={newKeyName}
            onChange={e => onNameChange(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && onCreateKey()}
            className="flex-1 bg-[#0d1117] border border-[#1e2329] rounded-lg px-3 py-2 text-xs text-white placeholder:text-[#4a5568] focus:outline-none focus:border-emerald-500/50 transition-colors"
          />
          <button
            onClick={onCreateKey}
            className="flex items-center gap-1.5 px-3 py-2 bg-emerald-500 hover:bg-emerald-400 text-black text-xs rounded-lg transition-colors font-semibold"
          >
            <Plus className="w-3 h-3" />
            Generate
          </button>
        </div>
        {isLoading ? (
          <p className="text-xs text-muted-foreground">Loading keys…</p>
        ) : apiKeys.length === 0 ? (
          <p className="text-xs text-muted-foreground">No API keys yet</p>
        ) : (
          <div className="space-y-2">
            {apiKeys.map((k: ApiKeyOut) => (
              <div key={k.id} className="flex items-center justify-between p-3 bg-[#0d1117] border border-[#1e2329] rounded-lg text-xs">
                <div className="flex items-center space-x-3">
                  <Key className="w-3.5 h-3.5 text-muted-foreground" />
                  <div>
                    <p className="text-white font-medium">{k.name}</p>
                    <p className="text-[10px] text-muted-foreground font-mono">{k.prefix}••••••••</p>
                  </div>
                </div>
                <div className="flex items-center space-x-3">
                  <span className="text-[10px] text-muted-foreground">{k.lastUsedAt ? formatDate(k.lastUsedAt) : 'Never used'}</span>
                  <button onClick={() => onRevokeKey(k.id)} className="text-red-500 hover:text-red-400 transition-colors" title="Revoke">
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </SectionCard>
    </div>
  );
}

function SecurityPanel({ sessions, onRevokeSession }: any) {
  const formatDate = (iso: string) => {
    try { return new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' }); }
    catch { return iso; }
  };
  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-base font-bold text-white">Security</h2>
        <p className="text-xs text-[#4a5568] mt-0.5">Active sessions across all devices.</p>
      </div>
      <SectionCard title="Active Sessions">
        {sessions.length === 0 ? (
          <p className="text-xs text-muted-foreground">No active sessions</p>
        ) : (
          sessions.map((s: SessionOut) => (
            <div key={s.id} className="flex items-center justify-between p-3 bg-[#0d1117] border border-[#1e2329] rounded-lg text-xs">
              <div className="flex items-center space-x-3">
                <Shield className="w-3.5 h-3.5 text-muted-foreground" />
                <div>
                  <p className="text-white font-medium">{s.ipAddress || 'Unknown IP'}</p>
                  <p className="text-[10px] text-muted-foreground truncate max-w-[200px]">{s.userAgent || 'Unknown browser'}</p>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <span className="text-[10px] text-muted-foreground">{formatDate(s.lastSeenAt)}</span>
                <button onClick={() => onRevokeSession(s.id)} className="text-red-500 hover:text-red-400 transition-colors" title="Revoke session">
                  <LogOut className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          ))
        )}
      </SectionCard>
    </div>
  );
}

function ConnectorsDashboardPanel() {
  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-base font-bold text-white">Connectors</h2>
        <p className="text-xs text-[#4a5568] mt-0.5">Sync data from Google Drive, Notion, Confluence, and more.</p>
      </div>
      <ConnectorsPanel />
    </div>
  );
}

// ── Main Page ──────────────────────────────────────────────────────────────────

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<CCTab>('providers');

  // Legacy state (preserved exactly)
  const [apiKeys, setApiKeys] = useState<ApiKeyOut[]>([]);
  const [sessions, setSessions] = useState<SessionOut[]>([]);
  const [newKeyName, setNewKeyName] = useState('');
  const [createdKey, setCreatedKey] = useState<string | null>(null);
  const [showKey, setShowKey] = useState(false);
  const [isLoadingKeys, setIsLoadingKeys] = useState(true);
  const [toastMsg, setToastMsg] = useState<string | null>(null);
  const [isRequestingReset, setIsRequestingReset] = useState(false);

  const userInfo = getUserInfo();
  const roles = getRoles();

  const showToast = (msg: string) => {
    setToastMsg(msg);
    setTimeout(() => setToastMsg(null), 3000);
  };

  const fetchAll = useCallback(async () => {
    setIsLoadingKeys(true);
    try {
      const [keys, sess] = await Promise.allSettled([
        settingsApi.listApiKeys(),
        settingsApi.listSessions(),
      ]);
      if (keys.status === 'fulfilled') setApiKeys(keys.value);
      if (sess.status === 'fulfilled') setSessions(sess.value);
    } finally {
      setIsLoadingKeys(false);
    }
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  const handleCreateKey = async () => {
    if (!newKeyName.trim()) return;
    try {
      const result = await settingsApi.createApiKey(newKeyName.trim());
      setCreatedKey(result.key);
      setNewKeyName('');
      setApiKeys(prev => [...prev, { id: result.id, name: result.name, prefix: result.key.slice(0, 10), lastUsedAt: null, createdAt: new Date().toISOString() }]);
      showToast('API key created');
    } catch { showToast('Failed to create API key'); }
  };

  const handleRevokeKey = async (keyId: string) => {
    try {
      await settingsApi.revokeApiKey(keyId);
      setApiKeys(prev => prev.filter(k => k.id !== keyId));
      showToast('API key revoked');
    } catch { showToast('Failed to revoke key'); }
  };

  const handleRevokeSession = async (sessionId: string) => {
    try {
      await settingsApi.revokeSession(sessionId);
      setSessions(prev => prev.filter(s => s.id !== sessionId));
      showToast('Session revoked');
    } catch { showToast('Failed to revoke session'); }
  };

  const handlePasswordReset = async () => {
    if (!userInfo?.email) return;
    setIsRequestingReset(true);
    try {
      await postRequestPasswordReset({ email: userInfo.email });
      showToast('Password reset link sent to email');
    } catch { showToast('Failed to request password reset'); } finally {
      setIsRequestingReset(false);
    }
  };

  const copyToClipboard = (text: string) =>
    navigator.clipboard.writeText(text).then(() => showToast('Copied!'));

  // ── Right sidebar ────────────────────────────────────────────────────────────
  const rightSidebar = (
    <div className="h-full flex flex-col">
      <HealthSidebar />
      <UsageSidebar days={7} />
    </div>
  );

  // ── Tab content ──────────────────────────────────────────────────────────────
  const renderContent = () => {
    switch (activeTab) {
      case 'providers':   return <LLMProvidersPanel />;
      case 'models':      return <ModelHubPanel />;
      case 'embeddings':  return <EmbeddingProvidersPanel />;
      case 'search':      return <SearchProvidersPanel />;
      case 'connectors':  return <ConnectorsDashboardPanel />;
      case 'runtime':     return <RuntimeConfigPanel />;
      case 'keys':
        return (
          <ApiKeysPanel
            apiKeys={apiKeys} newKeyName={newKeyName} createdKey={createdKey}
            showKey={showKey} isLoading={isLoadingKeys}
            onCreateKey={handleCreateKey} onRevokeKey={handleRevokeKey}
            onNameChange={setNewKeyName} onShowToggle={() => setShowKey(v => !v)}
            onCopy={copyToClipboard} onDismiss={() => setCreatedKey(null)}
          />
        );
      case 'security':
        return <SecurityPanel sessions={sessions} onRevokeSession={handleRevokeSession} />;
      case 'account':
        return (
          <AccountPanel
            userInfo={userInfo} roles={roles}
            onReset={handlePasswordReset} isResetting={isRequestingReset}
          />
        );
      default: return null;
    }
  };

  return (
    <RequireAuth>
      <div className="flex flex-col h-full bg-background relative overflow-hidden">
        <TopBar title="Settings" />

        {/* Toast */}
        {toastMsg && (
          <div className="fixed bottom-6 right-6 z-50 bg-emerald-500 text-black text-xs px-4 py-2 rounded-lg shadow-lg font-medium">
            {toastMsg}
          </div>
        )}

        {/* Control Center Layout — fills remaining height */}
        <div className="flex-1 overflow-hidden">
          <ControlCenterLayout
            activeTab={activeTab}
            onTabChange={setActiveTab}
            rightSidebar={rightSidebar}
          >
            {renderContent()}
          </ControlCenterLayout>
        </div>
      </div>
    </RequireAuth>
  );
}
