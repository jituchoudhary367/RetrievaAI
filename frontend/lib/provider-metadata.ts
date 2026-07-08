// lib/provider-metadata.ts
// Static metadata, logos (SVG inline), and schemas for all supported providers

export type ProviderCapability = 'streaming' | 'vision' | 'json_mode' | 'function_calling' | 'reasoning' | 'local_only';

export interface LLMProviderMeta {
  id: string;
  name: string;
  logo: string; // SVG string
  color: string; // brand accent
  description: string;
  capabilities: ProviderCapability[];
  isLocalOnly?: boolean;
  fields: ProviderField[];
  docUrl: string;
}

export interface EmbeddingProviderMeta {
  id: string;
  name: string;
  logo: string;
  color: string;
  description: string;
  isLocal: boolean;
  defaultDimensions: number;
  fields: ProviderField[];
}

export interface SearchProviderMeta {
  id: string;
  name: string;
  logo: string;
  color: string;
  description: string;
  isFree: boolean;
  fields: ProviderField[];
}

export interface ProviderField {
  key: string;
  label: string;
  type: 'text' | 'password' | 'number' | 'url' | 'select' | 'toggle';
  placeholder?: string;
  required?: boolean;
  options?: string[];
  min?: number;
  max?: number;
  step?: number;
  hidden?: boolean; // hide for local providers
}

// ── SVG Logos ─────────────────────────────────────────────────────────────────

const GROQ_LOGO = `<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="12" cy="12" r="12" fill="#F55036"/><text x="12" y="16" text-anchor="middle" fill="white" font-size="10" font-weight="bold" font-family="sans-serif">G</text></svg>`;
const OPENAI_LOGO = `<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path fill="currentColor" d="M22.282 9.821a5.985 5.985 0 0 0-.516-4.91 6.046 6.046 0 0 0-6.51-2.9A6.065 6.065 0 0 0 4.981 4.18a5.985 5.985 0 0 0-3.998 2.9 6.046 6.046 0 0 0 .743 7.097 5.98 5.98 0 0 0 .51 4.911 6.051 6.051 0 0 0 6.515 2.9A5.985 5.985 0 0 0 13.26 24a6.056 6.056 0 0 0 5.772-4.206 5.99 5.99 0 0 0 3.997-2.9 6.056 6.056 0 0 0-.747-7.073zM13.26 22.43a4.476 4.476 0 0 1-2.876-1.04l.141-.081 4.779-2.758a.795.795 0 0 0 .392-.681v-6.737l2.02 1.168a.071.071 0 0 1 .038.052v5.583a4.504 4.504 0 0 1-4.494 4.494zM3.6 18.304a4.47 4.47 0 0 1-.535-3.014l.142.085 4.783 2.759a.771.771 0 0 0 .78 0l5.843-3.369v2.332a.08.08 0 0 1-.033.062L9.74 19.95a4.5 4.5 0 0 1-6.14-1.646zM2.34 7.896a4.485 4.485 0 0 1 2.366-1.973V11.6a.766.766 0 0 0 .388.676l5.815 3.355-2.02 1.168a.076.076 0 0 1-.071 0l-4.83-2.786A4.504 4.504 0 0 1 2.34 7.872zm16.597 3.855l-5.843-3.372L15.105 7.2a.076.076 0 0 1 .071 0l4.83 2.791a4.494 4.494 0 0 1-.676 8.105v-5.678a.79.79 0 0 0-.393-.667zm2.01-3.023l-.141-.085-4.774-2.782a.776.776 0 0 0-.785 0L9.409 9.23V6.897a.066.066 0 0 1 .028-.061l4.83-2.787a4.5 4.5 0 0 1 6.68 4.66zm-12.64 4.135l-2.02-1.164a.08.08 0 0 1-.038-.057V6.075a4.5 4.5 0 0 1 7.375-3.453l-.142.08-4.778 2.758a.795.795 0 0 0-.393.681zm1.097-2.365l2.602-1.5 2.607 1.5v2.999l-2.597 1.5-2.607-1.5z"/></svg>`;
const ANTHROPIC_LOGO = `<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><rect width="24" height="24" rx="4" fill="#CC785C"/><text x="12" y="16" text-anchor="middle" fill="white" font-size="11" font-weight="bold" font-family="sans-serif">A</text></svg>`;
const GEMINI_LOGO = `<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><defs><linearGradient id="g1" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" style="stop-color:#4285F4"/><stop offset="100%" style="stop-color:#EA4335"/></linearGradient></defs><path fill="url(#g1)" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-1-13h2v6h-2zm0 8h2v2h-2z"/></svg>`;
const OPENROUTER_LOGO = `<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><circle cx="12" cy="12" r="12" fill="#6C47FF"/><text x="12" y="16" text-anchor="middle" fill="white" font-size="9" font-weight="bold" font-family="sans-serif">OR</text></svg>`;
const DEEPSEEK_LOGO = `<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><circle cx="12" cy="12" r="12" fill="#0066FF"/><text x="12" y="16" text-anchor="middle" fill="white" font-size="9" font-weight="bold" font-family="sans-serif">DS</text></svg>`;
const AZURE_LOGO = `<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path fill="#0089D6" d="M13.05 4.24L6.56 18.05l-3.19.01 6.41-12.57zm.71 0l3.85 9.9-7.65 2.07 7.13-1.56L13.76 4.24zm2.48 11.02l2.17 2.79H5.37l4.15-2.24z"/></svg>`;
const OLLAMA_LOGO = `<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><circle cx="12" cy="12" r="12" fill="#222"/><circle cx="9" cy="11" r="2" fill="white"/><circle cx="15" cy="11" r="2" fill="white"/><path d="M9 15 Q12 17 15 15" stroke="white" stroke-width="1" fill="none"/></svg>`;
const COHERE_LOGO = `<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><circle cx="12" cy="12" r="12" fill="#39594D"/><text x="12" y="16" text-anchor="middle" fill="white" font-size="9" font-weight="bold" font-family="sans-serif">CO</text></svg>`;
const SERPER_LOGO = `<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><circle cx="12" cy="12" r="12" fill="#1E88E5"/><text x="12" y="16" text-anchor="middle" fill="white" font-size="9" font-weight="bold" font-family="sans-serif">Se</text></svg>`;
const TAVILY_LOGO = `<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><circle cx="12" cy="12" r="12" fill="#00BFA5"/><text x="12" y="16" text-anchor="middle" fill="white" font-size="9" font-weight="bold" font-family="sans-serif">Tv</text></svg>`;
const BRAVE_LOGO = `<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><circle cx="12" cy="12" r="12" fill="#FB542B"/><text x="12" y="16" text-anchor="middle" fill="white" font-size="9" font-weight="bold" font-family="sans-serif">B</text></svg>`;
const EXA_LOGO = `<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><circle cx="12" cy="12" r="12" fill="#7C3AED"/><text x="12" y="16" text-anchor="middle" fill="white" font-size="9" font-weight="bold" font-family="sans-serif">Ex</text></svg>`;
const DDG_LOGO = `<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><circle cx="12" cy="12" r="12" fill="#DE5833"/><text x="12" y="16" text-anchor="middle" fill="white" font-size="8" font-weight="bold" font-family="sans-serif">DDG</text></svg>`;

// ── LLM Provider Metadata ─────────────────────────────────────────────────────

export const LLM_PROVIDERS: LLMProviderMeta[] = [
  {
    id: 'groq',
    name: 'Groq',
    logo: GROQ_LOGO,
    color: '#F55036',
    description: 'Ultra-fast LPU inference. Best for low-latency applications.',
    capabilities: ['streaming', 'function_calling', 'json_mode'],
    fields: [
      { key: 'api_key', label: 'API Key', type: 'password', placeholder: 'gsk_...', required: true },
      { key: 'model', label: 'Default Model', type: 'text', placeholder: 'llama-3.3-70b-versatile' },
      { key: 'temperature', label: 'Temperature', type: 'number', min: 0, max: 2, step: 0.1 },
      { key: 'max_tokens', label: 'Max Tokens', type: 'number', min: 1, max: 32768 },
      { key: 'streaming', label: 'Streaming', type: 'toggle' },
    ],
    docUrl: 'https://console.groq.com',
  },
  {
    id: 'openai',
    name: 'OpenAI',
    logo: OPENAI_LOGO,
    color: '#10b981',
    description: 'GPT-4o, o3, and more. Best overall quality.',
    capabilities: ['streaming', 'vision', 'json_mode', 'function_calling', 'reasoning'],
    fields: [
      { key: 'api_key', label: 'API Key', type: 'password', placeholder: 'sk-...', required: true },
      { key: 'organization_id', label: 'Organization ID', type: 'text', placeholder: 'org-...' },
      { key: 'model', label: 'Default Model', type: 'text', placeholder: 'gpt-4o-mini' },
      { key: 'temperature', label: 'Temperature', type: 'number', min: 0, max: 2, step: 0.1 },
      { key: 'max_tokens', label: 'Max Tokens', type: 'number', min: 1, max: 128000 },
      { key: 'streaming', label: 'Streaming', type: 'toggle' },
    ],
    docUrl: 'https://platform.openai.com',
  },
  {
    id: 'anthropic',
    name: 'Anthropic',
    logo: ANTHROPIC_LOGO,
    color: '#CC785C',
    description: 'Claude models. Best for reasoning and long context.',
    capabilities: ['streaming', 'vision', 'function_calling', 'reasoning'],
    fields: [
      { key: 'api_key', label: 'API Key', type: 'password', placeholder: 'sk-ant-...', required: true },
      { key: 'model', label: 'Default Model', type: 'text', placeholder: 'claude-3-5-haiku-20241022' },
      { key: 'temperature', label: 'Temperature', type: 'number', min: 0, max: 1, step: 0.1 },
      { key: 'max_tokens', label: 'Max Tokens', type: 'number', min: 1, max: 200000 },
      { key: 'streaming', label: 'Streaming', type: 'toggle' },
    ],
    docUrl: 'https://console.anthropic.com',
  },
  {
    id: 'gemini',
    name: 'Google Gemini',
    logo: GEMINI_LOGO,
    color: '#4285F4',
    description: 'Gemini models. Best for multimodal and long context.',
    capabilities: ['streaming', 'vision', 'function_calling', 'json_mode'],
    fields: [
      { key: 'api_key', label: 'API Key', type: 'password', placeholder: 'AIza...', required: true },
      { key: 'model', label: 'Default Model', type: 'text', placeholder: 'gemini-2.0-flash' },
      { key: 'temperature', label: 'Temperature', type: 'number', min: 0, max: 2, step: 0.1 },
      { key: 'max_tokens', label: 'Max Tokens', type: 'number', min: 1, max: 8192 },
    ],
    docUrl: 'https://aistudio.google.com',
  },
  {
    id: 'openrouter',
    name: 'OpenRouter',
    logo: OPENROUTER_LOGO,
    color: '#6C47FF',
    description: 'Access 200+ models through a single API. Includes free tier.',
    capabilities: ['streaming', 'vision', 'function_calling'],
    fields: [
      { key: 'api_key', label: 'API Key', type: 'password', placeholder: 'sk-or-...', required: true },
      { key: 'model', label: 'Default Model', type: 'text', placeholder: 'meta-llama/llama-3.1-8b-instruct:free' },
      { key: 'temperature', label: 'Temperature', type: 'number', min: 0, max: 2, step: 0.1 },
      { key: 'max_tokens', label: 'Max Tokens', type: 'number', min: 1, max: 128000 },
    ],
    docUrl: 'https://openrouter.ai',
  },
  {
    id: 'deepseek',
    name: 'DeepSeek',
    logo: DEEPSEEK_LOGO,
    color: '#0066FF',
    description: 'Top-tier reasoning at very low cost. Excellent for coding.',
    capabilities: ['streaming', 'reasoning', 'json_mode'],
    fields: [
      { key: 'api_key', label: 'API Key', type: 'password', placeholder: 'sk-...', required: true },
      { key: 'model', label: 'Default Model', type: 'text', placeholder: 'deepseek-chat' },
      { key: 'temperature', label: 'Temperature', type: 'number', min: 0, max: 2, step: 0.1 },
      { key: 'max_tokens', label: 'Max Tokens', type: 'number', min: 1, max: 65536 },
    ],
    docUrl: 'https://platform.deepseek.com',
  },
  {
    id: 'azure_openai',
    name: 'Azure OpenAI',
    logo: AZURE_LOGO,
    color: '#0089D6',
    description: 'OpenAI models hosted on Azure. Enterprise SLAs.',
    capabilities: ['streaming', 'vision', 'json_mode', 'function_calling'],
    fields: [
      { key: 'api_key', label: 'API Key', type: 'password', required: true },
      { key: 'endpoint', label: 'Endpoint URL', type: 'url', placeholder: 'https://xxx.openai.azure.com', required: true },
      { key: 'model', label: 'Deployment Name', type: 'text', placeholder: 'gpt-4o', required: true },
      { key: 'api_version', label: 'API Version', type: 'text', placeholder: '2024-02-01' },
      { key: 'temperature', label: 'Temperature', type: 'number', min: 0, max: 2, step: 0.1 },
      { key: 'max_tokens', label: 'Max Tokens', type: 'number', min: 1, max: 128000 },
    ],
    docUrl: 'https://azure.microsoft.com/en-us/products/ai-services/openai-service',
  },
  {
    id: 'ollama',
    name: 'Ollama',
    logo: OLLAMA_LOGO,
    color: '#555',
    description: 'Run LLMs locally. Privacy-first, no API key needed.',
    capabilities: ['streaming', 'local_only'],
    isLocalOnly: true,
    fields: [
      { key: 'endpoint', label: 'Endpoint URL', type: 'url', placeholder: 'http://localhost:11434' },
      { key: 'model', label: 'Default Model', type: 'text', placeholder: 'llama3.2' },
      { key: 'temperature', label: 'Temperature', type: 'number', min: 0, max: 2, step: 0.1 },
    ],
    docUrl: 'https://ollama.com',
  },
];

// ── Embedding Provider Metadata ───────────────────────────────────────────────

export const EMBEDDING_PROVIDERS: EmbeddingProviderMeta[] = [
  {
    id: 'cohere',
    name: 'Cohere',
    logo: COHERE_LOGO,
    color: '#39594D',
    description: 'embed-english-v3.0. 1024 dims, excellent quality, free tier.',
    isLocal: false,
    defaultDimensions: 1024,
    fields: [
      { key: 'api_key', label: 'API Key', type: 'password', required: true },
      { key: 'model', label: 'Model', type: 'text', placeholder: 'embed-english-v3.0' },
      { key: 'dimensions', label: 'Dimensions', type: 'number', min: 64 },
    ],
  },
  {
    id: 'openai_embed',
    name: 'OpenAI Embeddings',
    logo: OPENAI_LOGO,
    color: '#10b981',
    description: 'text-embedding-3-small / large. High quality, paid.',
    isLocal: false,
    defaultDimensions: 1536,
    fields: [
      { key: 'api_key', label: 'API Key', type: 'password', required: true },
      { key: 'model', label: 'Model', type: 'select', options: ['text-embedding-3-small', 'text-embedding-3-large', 'text-embedding-ada-002'] },
      { key: 'dimensions', label: 'Dimensions', type: 'number', min: 64 },
    ],
  },
  {
    id: 'voyage',
    name: 'Voyage AI',
    logo: `<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="12" fill="#1A1A2E"/><text x="12" y="16" text-anchor="middle" fill="white" font-size="8" font-weight="bold" font-family="sans-serif">VOY</text></svg>`,
    color: '#1A1A2E',
    description: 'voyage-3 series. State-of-the-art retrieval quality.',
    isLocal: false,
    defaultDimensions: 1024,
    fields: [
      { key: 'api_key', label: 'API Key', type: 'password', required: true },
      { key: 'model', label: 'Model', type: 'text', placeholder: 'voyage-3-lite' },
      { key: 'dimensions', label: 'Dimensions', type: 'number', min: 64 },
    ],
  },
  {
    id: 'jina',
    name: 'Jina AI',
    logo: `<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="12" fill="#009999"/><text x="12" y="16" text-anchor="middle" fill="white" font-size="9" font-weight="bold" font-family="sans-serif">Ji</text></svg>`,
    color: '#009999',
    description: 'jina-embeddings-v3. Multi-task, multi-lingual.',
    isLocal: false,
    defaultDimensions: 1024,
    fields: [
      { key: 'api_key', label: 'API Key', type: 'password', required: true },
      { key: 'model', label: 'Model', type: 'text', placeholder: 'jina-embeddings-v3' },
    ],
  },
  {
    id: 'huggingface',
    name: 'Local HuggingFace',
    logo: `<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="12" fill="#FFD21E"/><text x="12" y="16" text-anchor="middle" fill="#333" font-size="12">🤗</text></svg>`,
    color: '#FFD21E',
    description: 'Run any sentence-transformer locally. No API key needed.',
    isLocal: true,
    defaultDimensions: 1024,
    fields: [
      { key: 'model', label: 'Model Name', type: 'text', placeholder: 'BAAI/bge-m3' },
      { key: 'dimensions', label: 'Dimensions', type: 'number', min: 64 },
    ],
  },
];

// ── Search Provider Metadata ──────────────────────────────────────────────────

export const SEARCH_PROVIDERS: SearchProviderMeta[] = [
  {
    id: 'duckduckgo',
    name: 'DuckDuckGo',
    logo: DDG_LOGO,
    color: '#DE5833',
    description: 'Privacy-focused search. No API key required. Default.',
    isFree: true,
    fields: [
      { key: 'max_results', label: 'Max Results', type: 'number', min: 1, max: 20 },
      { key: 'timeout', label: 'Timeout (s)', type: 'number', min: 5, max: 60 },
    ],
  },
  {
    id: 'serper',
    name: 'Serper',
    logo: SERPER_LOGO,
    color: '#1E88E5',
    description: 'Google Search API. High quality, fast, generous free tier.',
    isFree: false,
    fields: [
      { key: 'api_key', label: 'API Key', type: 'password', required: true },
      { key: 'max_results', label: 'Max Results', type: 'number', min: 1, max: 20 },
    ],
  },
  {
    id: 'tavily',
    name: 'Tavily',
    logo: TAVILY_LOGO,
    color: '#00BFA5',
    description: 'AI-optimized search with clean summaries. Built for RAG.',
    isFree: false,
    fields: [
      { key: 'api_key', label: 'API Key', type: 'password', required: true },
      { key: 'max_results', label: 'Max Results', type: 'number', min: 1, max: 20 },
    ],
  },
  {
    id: 'brave',
    name: 'Brave Search',
    logo: BRAVE_LOGO,
    color: '#FB542B',
    description: 'Independent search index. Privacy-focused, fast.',
    isFree: false,
    fields: [
      { key: 'api_key', label: 'API Key', type: 'password', required: true },
      { key: 'max_results', label: 'Max Results', type: 'number', min: 1, max: 20 },
    ],
  },
  {
    id: 'exa',
    name: 'Exa',
    logo: EXA_LOGO,
    color: '#7C3AED',
    description: 'Neural search for the web. Semantic, not keyword-based.',
    isFree: false,
    fields: [
      { key: 'api_key', label: 'API Key', type: 'password', required: true },
      { key: 'max_results', label: 'Max Results', type: 'number', min: 1, max: 20 },
    ],
  },
];

// ── Helpers ───────────────────────────────────────────────────────────────────

export function getLLMProviderMeta(id: string): LLMProviderMeta | undefined {
  return LLM_PROVIDERS.find(p => p.id === id);
}

export function getEmbeddingProviderMeta(id: string): EmbeddingProviderMeta | undefined {
  return EMBEDDING_PROVIDERS.find(p => p.id === id);
}

export function getSearchProviderMeta(id: string): SearchProviderMeta | undefined {
  return SEARCH_PROVIDERS.find(p => p.id === id);
}

export const CAPABILITY_LABELS: Record<ProviderCapability, string> = {
  streaming: 'Streaming',
  vision: 'Vision',
  json_mode: 'JSON Mode',
  function_calling: 'Function Calling',
  reasoning: 'Reasoning',
  local_only: 'Local Only',
};
