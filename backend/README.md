# RAG API Service

This is the backend for the RAG (Retrieval-Augmented Generation) application, providing document ingestion, vector/sparse search, and a conversational LLM pipeline.

## Environment Variables

The application is configured primarily through environment variables, which can be provided via a `.env` file at the root of the project. The settings are grouped into the following sections defined in `app/config.py`:

### Application Settings (No prefix)
* `ENV`: Environment mode (development, staging, production, test). Defaults to `development`.
* `DEBUG`: Enable debug mode. Defaults to `false`.
* `API_V1_PREFIX`: Prefix for API routes. Defaults to `/api`.

### Redis Settings (Prefix `REDIS_`)
* `REDIS_HOST`: Redis server host (default: `localhost`).
* `REDIS_PORT`: Redis server port (default: `6379`).
* `REDIS_DB`: Redis database index (default: `0`).
* `REDIS_PASSWORD`: Optional Redis password.
* `REDIS_SSL`: Use SSL for Redis connection (default: `false`).
* `REDIS_SOCKET_TIMEOUT`: Socket timeout in seconds (default: `5.0`).
* `REDIS_SOCKET_CONNECT_TIMEOUT`: Connection timeout in seconds (default: `5.0`).
* `REDIS_MAX_CONNECTIONS`: Max connections pool size (default: `50`).
* `REDIS_HEALTH_CHECK_INTERVAL`: Health check interval (default: `30`).
* `REDIS_CACHE_TTL_SECONDS`: Semantic cache TTL (default: `3600`).
* `REDIS_CACHE_SIMILARITY_THRESHOLD`: Threshold for cache hit (default: `0.95`).
* `REDIS_CACHE_KEY_PREFIX`: Cache prefix (default: `rag:cache:`).

### Qdrant Settings (Prefix `QDRANT_`)
* `QDRANT_HOST`: Qdrant server host (default: `localhost`).
* `QDRANT_PORT`: Qdrant server port (default: `6333`).
* `QDRANT_API_KEY`: Optional API key.
* `QDRANT_COLLECTION_NAME`: Target collection name (default: `rag_documents`).
* `QDRANT_VECTOR_SIZE`: Dense vector size (default: `768`).
* `QDRANT_DISTANCE_METRIC`: Vector distance metric (default: `Cosine`).
* `QDRANT_BM25_INDEX_PATH`: Path to persisted BM25 index (default: `./data/bm25_index.pkl`).

### LLM Settings (Prefix `LLM_`)
* `LLM_PROVIDER`: Provider (openai, anthropic, azure_openai, ollama). Default: `openai`.
* `LLM_API_KEY`: API key for the chosen provider.
* `LLM_MODEL_NAME`: Chat model name (e.g., `gpt-4o`).
* `LLM_MAX_TOKENS`: Max tokens for generation (default: `2048`).
* `LLM_TEMPERATURE`: Default temperature (default: `0.1`).
* `LLM_BASE_URL`: Optional custom base URL for the API.

### Embedding Settings (Prefix `EMBED_`)
* `EMBED_PROVIDER`: Provider (openai, huggingface, cohere). Default: `huggingface`.
* `EMBED_MODEL_NAME`: Embedding model name (default: `BAAI/bge-base-en-v1.5`).
* `EMBED_API_KEY`: API key if required by provider.
* `EMBED_DIMENSIONS`: Output dimensions (default: `768`).
* `EMBED_BATCH_SIZE`: Batch size for embedding (default: `32`).

### Ingestion Settings (Prefix `INGEST_`)
* `INGEST_CHUNK_STRATEGY`: Strategy (recursive, semantic, ast, markdown). Default: `recursive`.
* `INGEST_CHUNK_SIZE`: Target chunk size (default: `1000`).
* `INGEST_CHUNK_OVERLAP`: Overlap between chunks (default: `200`).
* `INGEST_EXTRACT_IMAGES`: Enable image extraction (default: `false`).
* `INGEST_EXTRACT_TABLES`: Enable table extraction (default: `true`).

### Retrieval Settings (Prefix `RETRIEVAL_`)
* `RETRIEVAL_TOP_K_DENSE`: Top K dense hits (default: `20`).
* `RETRIEVAL_TOP_K_SPARSE`: Top K sparse hits (default: `20`).
* `RETRIEVAL_TOP_K_FINAL`: Final top K after fusion (default: `10`).
* `RETRIEVAL_HYBRID_ALPHA`: Weight for dense scores in fusion (default: `0.5`).
* `RETRIEVAL_RRF_K`: Constant K for Reciprocal Rank Fusion (default: `60`).
* `RETRIEVAL_RERANK_ENABLED`: Enable cross-encoder reranking (default: `false`).
* `RETRIEVAL_RERANK_MODEL`: Reranker model name (default: `cross-encoder/ms-marco-MiniLM-L-6-v2`).

### Feature Flags (Prefix `FEATURE_`)
* `FEATURE_ENABLE_SEMANTIC_CACHE`: Enable semantic caching (default: `true`).
* `FEATURE_ENABLE_CRAG`: Enable CRAG agent flow (default: `true`).
* `FEATURE_ENABLE_WEB_SEARCH_FALLBACK`: Enable web search fallback (default: `false`).
* `FEATURE_ENABLE_GUARDRAILS`: Enable input/output guardrails (default: `true`).

### Security Settings (Prefix `SECURITY_`)
* `SECURITY_API_KEYS`: List of valid static API keys for the service.
* `SECURITY_ALLOWED_ORIGINS`: Allowed CORS origins (default: `["*"]`).
* `SECURITY_MAX_REQUEST_SIZE_BYTES`: Max size for ingestion payload (default: `10485760`).
* `SECURITY_PII_FILTERING_ENABLED`: Enable PII redaction (default: `false`).

---

## API Endpoints

### 1. Health Checks
`GET /health/live`
`GET /health/ready`
Provides liveness and readiness probes indicating the status of the service and its dependencies (Redis, Qdrant).
**Response Shape:** `app.models.HealthResponse`

### 2. Search
`POST /api/search`
Retrieval-only endpoint (no LLM generation). Uses hybrid search (dense + sparse) and optional cross-encoder reranking to return the most relevant chunks.
**Request Shape:** `app.models.SearchRequest`
**Response Shape:** `app.models.SearchResponse`

### 3. Query
`POST /api/query`
Conversational RAG endpoint. Incorporates retrieval, context formatting, and LLM answer generation. Supports both streaming and non-streaming responses.
**Request Shape:** `app.models.QueryRequest`
**Response Shape:** `app.models.ChatResponse` (if non-streaming) or SSE stream of `app.models.StreamChunk` (if streaming)

---

## Deployment Setup

### Local Development (`docker-compose.yml`)
You can spin up the full service alongside its dependencies (Redis, Qdrant) locally:
```bash
docker-compose up --build
```
This mounts a named volume for Qdrant storage (`qdrant_data`) and a shared volume for the BM25 index path.

### Production (`docker-compose.prod.yml`)
For production, use the prod compose override to enable GPU reservations, enforce restart policies, and set strict resource limits:
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```
You can inject specific extra dependencies into the `Dockerfile` at build time using `--build-arg INSTALL_EXTRAS="pdf html"`.

---

## Troubleshooting Optional Dependencies

The application uses optional dependencies (extras) to keep the base footprint minimal. If you receive an `ImportError` for an optional module, make sure you install the appropriate extra package group or base library.

- **`pdfplumber` / `pdf2image` / `pytesseract` (PDF Extraction)**: Install via `pip install ".[pdf]"`. Ensure `poppler-utils` and `tesseract-ocr` system packages are also installed for OCR to work.
- **`trafilatura` / `bs4` (HTML Extraction)**: Install via `pip install ".[html]"`.
- **`docx` (DOCX Extraction)**: Install via `pip install ".[docx]"`.
- **`PIL` / `pytesseract` (Image Extraction)**: Install via `pip install ".[image]"`. Requires system `tesseract-ocr`.
- **`sentence-transformers` (Embedder / Reranker)**: Install via `pip install ".[local-models]"`.
- **`semantic-chunkers` (Semantic Chunker)**: Install via `pip install ".[chunking]"`.
- **`tree_sitter` / `tree_sitter_python` (AST Chunker)**: Install via `pip install ".[ast]"`.
- **`duckduckgo_search` / `googlesearch-python` (Web Search Tool)**: Install via `pip install ".[web]"`.
- **`qdrant-client` (Qdrant Indexer)**: Install via `pip install ".[qdrant]"`.
- **`rank_bm25` (BM25 Indexer)**: Install via `pip install ".[bm25]"`.
- **`redis` (Semantic Cache / Conversation Store)**: Install via `pip install ".[redis]"`.
