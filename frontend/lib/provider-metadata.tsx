// lib/provider-metadata.ts
// Static metadata, logos (SVG inline), and schemas for all supported providers

export type ProviderCapability = 'streaming' | 'vision' | 'json_mode' | 'function_calling' | 'reasoning' | 'local_only';

export interface LLMProviderMeta {
  id: string;
  name: string;
  logo: React.ReactNode;
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
  logo: React.ReactNode;
  color: string;
  description: string;
  isLocal: boolean;
  defaultDimensions: number;
  fields: ProviderField[];
}

export interface SearchProviderMeta {
  id: string;
  name: string;
  logo: React.ReactNode;
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

import React from 'react';
import {
  SiGoogle, 
  SiAnthropic,
  SiDuckduckgo,
  SiBrave,
} from 'react-icons/si';
import { TbBrandAzure, TbBrandOpenai } from 'react-icons/tb';

const GROQ_LOGO = <div className="w-full h-full bg-[#F55036] rounded-full flex items-center justify-center text-white font-bold text-[10px]">G</div>;
const OPENAI_LOGO = <TbBrandOpenai className="w-full h-full text-[#10b981]" />;
const ANTHROPIC_LOGO = <SiAnthropic className="w-full h-full text-[#CC785C]" />;
const GEMINI_LOGO = <SiGoogle className="w-full h-full text-[#4285F4]" />;
const OPENROUTER_LOGO = <div className="w-full h-full bg-[#6C47FF] rounded-full flex items-center justify-center text-white font-bold text-[9px]">OR</div>;
const DEEPSEEK_LOGO = <div className="w-full h-full bg-[#0066FF] rounded-full flex items-center justify-center text-white font-bold text-[9px]">DS</div>;
const AZURE_LOGO = <TbBrandAzure className="w-full h-full text-[#0078d4]" />;
const OLLAMA_LOGO = <div className="w-full h-full bg-[#222] rounded-full flex items-center justify-center relative"><div className="w-1 h-1 bg-white rounded-full absolute left-2.5 top-2.5"></div><div className="w-1 h-1 bg-white rounded-full absolute right-2.5 top-2.5"></div><div className="absolute bottom-2.5 w-3 h-1.5 border-b-2 border-white rounded-full"></div></div>;
const COHERE_LOGO = <div className="w-full h-full bg-[#39594D] rounded-full flex items-center justify-center text-white font-bold text-[9px]">CO</div>;
const SERPER_LOGO = <div className="w-full h-full bg-[#1E88E5] rounded-full flex items-center justify-center text-white font-bold text-[9px]">Se</div>;
const TAVILY_LOGO = <div className="w-full h-full bg-[#00BFA5] rounded-full flex items-center justify-center text-white font-bold text-[9px]">Tv</div>;
const BRAVE_LOGO = <SiBrave className="w-full h-full text-[#FB542B]" />;
const EXA_LOGO = <div className="w-full h-full bg-[#7C3AED] rounded-full flex items-center justify-center text-white font-bold text-[9px]">Ex</div>;
const DDG_LOGO = <SiDuckduckgo className="w-full h-full text-[#DE5833]" />;

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
