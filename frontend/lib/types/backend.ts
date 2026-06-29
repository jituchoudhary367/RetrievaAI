export interface TokenResponse {
  accessToken: string;
  tokenType: string;
}

export interface User {
  id: string;
  email: string;
  role: string;
  tenantId: string;
  isActive: boolean;
}

export interface DocumentRow {
  id: string;
  title: string;
  sourceType: string;
  status: string;
  contentHash: string;
  chunkCount: number;
  metadata: any;
  createdAt: string;
  updatedAt: string;
}

export interface DocumentCreate {
  title: string;
  sourceType: string;
  metadata?: any;
}

export interface QueryEventRow {
  id: string;
  tenantId: string;
  userId: string;
  sessionId: string;
  queryText: string;
  intent: string;
  usedCache: boolean;
  totalLatencyMs: number;
  totalTokens: number;
  createdAt: string;
}

export interface ConversationRow {
  id: string;
  sessionId: string;
  title: string;
  createdAt: string;
  updatedAt: string;
}

export interface ConversationMessageRow {
  id: string;
  role: string;
  content: string;
  createdAt: string;
}

export interface ToolRow {
  id: string;
  name: string;
  category: string;
  description: string;
  status: string;
  isExecutable: boolean;
}

export interface ToolExecutionRow {
  id: string;
  toolId: string;
  status: string;
  latencyMs: number;
  errorMessage?: string;
  createdAt: string;
}

export interface TelemetryEventRow {
  id: string;
  eventType: string;
  eventData: any;
  createdAt: string;
}

export interface HealthSampleRow {
  id: string;
  status: string;
  latencyMs: number;
  cpuPercent: number;
  memoryMb: number;
  createdAt: string;
}

export interface SystemSettings {
  llmProvider: string;
  llmModelName: string;
  embeddingModel: string;
  maxRetries: number;
}
