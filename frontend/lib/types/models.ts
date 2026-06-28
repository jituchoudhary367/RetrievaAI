export type QueryIntent = "simple_qa" | "complex_qa" | "code_search" | "web_search" | "hybrid_search";
export type RelevanceGrade = "good" | "bad" | "need_web";
export type RetrievalSource = "vector" | "bm25" | "web" | "code" | "cache";
export type MessageRole = "system" | "user" | "assistant" | "tool";
export type StreamEventType = "start" | "token" | "citation" | "tool_call" | "tool_result" | "error" | "end";
export type HealthStatus = "healthy" | "degraded" | "unhealthy";

export interface MetadataFilter {
  field: string;
  value: any;
  operator: string;
}

export interface QueryRequest {
  query: string;
  sessionId?: string;
  conversationHistory?: ChatMessage[];
  filters?: MetadataFilter[];
  topK?: number;
  stream?: boolean;
  useCache?: boolean;
  temperature?: number;
  maxTokens?: number;
}

export interface ChatMessage {
  role: MessageRole;
  content: string;
  timestamp?: string;
  metadata?: Record<string, any>;
}

export interface SearchRequest {
  query: string;
  topK?: number;
  filters?: MetadataFilter[];
  rerank?: boolean;
  includeDebugInfo?: boolean;
}

export interface SearchResult {
  chunkId: string;
  documentId: string;
  text: string;
  score: number;
  source: RetrievalSource;
  metadata?: Record<string, any>;
}

export interface SearchResponse {
  query: string;
  results: SearchResult[];
  totalResults: number;
  latencyMs: number;
  debugInfo?: Record<string, any>;
}

export interface Citation {
  citationId: string;
  documentId: string;
  chunkId: string;
  source: RetrievalSource;
  textSnippet: string;
  score: number;
  pageNumber?: number;
  url?: string;
}

export interface TokenUsage {
  promptTokens: number;
  completionTokens: number;
  totalTokens: number;
}

export interface ResponseMetadata {
  intent?: QueryIntent;
  usedCache: boolean;
  usedWebSearch: boolean;
  usedCodeSearch: boolean;
  cragCorrections?: boolean;
  retrievalLatencyMs?: number;
  generationLatencyMs?: number;
  totalLatencyMs: number;
  tokenUsage?: TokenUsage;
  modelName?: string;
}

export interface ChatResponse {
  sessionId: string;
  answer: string;
  citations: Citation[];
  metadata: ResponseMetadata;
  createdAt: string;
}

export interface StreamChunk {
  event: StreamEventType;
  sessionId: string;
  sequence: number;
  delta?: string;
  citation?: Citation;
  toolName?: string;
  metadata?: ResponseMetadata;
  errorMessage?: string;
}

export interface ErrorDetail {
  code: string;
  message: string;
  field?: string;
}

export interface ErrorResponse {
  requestId: string;
  statusCode: number;
  errors: ErrorDetail[];
  timestamp: string;
}

export interface ComponentHealth {
  name: string;
  status: HealthStatus;
  detail?: string;
  latencyMs?: number;
}

export interface HealthResponse {
  status: HealthStatus;
  version: string;
  uptimeSeconds: number;
  components: ComponentHealth[];
}
