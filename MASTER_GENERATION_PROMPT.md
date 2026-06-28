# Master Generation Prompt — Production RAG Service

This document is the single source of truth for generating every remaining
file in this repository. It contains **no code** — only the exact contract
each file must satisfy so that every module imports correctly, every
function/class signature matches what its callers expect, and the system
wires together with zero integration errors on the first pass.

Follow the project structure **exactly as listed below**. Do not add, rename,
merge, or split any file or folder beyond what is specified.

---

## 0. Already Generated — Do Not Regenerate

These files exist and are final. Treat their public symbols as a fixed
contract that every new file must conform to.

| File | Status |
|---|---|
| `app/config.py` | ✅ Done — **needs one micro-patch before any other file is generated**, see §1. |
| `app/models.py` | ✅ Done |
| `Dockerfile` | ✅ Done |
| `pipeline/extractors/text_extractor.py` | ✅ Done (defines `BaseExtractor`, `ExtractionResult`, `ExtractionError`, `TextExtractor`) |

---

## 1. Required Pre-Fix to `app/config.py`

Before generating `pipeline/chunker.py`, patch `app/config.py`:

- Add a `ChunkingStrategy(str, Enum)` with members `RECURSIVE = "recursive"`,
  `SEMANTIC = "semantic"`, `AST = "ast"`, `MARKDOWN = "markdown"`, defined
  alongside the existing `LogFormat` enum.
- Change `ChunkingSettings.strategy` from `str` to `ChunkingStrategy`
  (default `ChunkingStrategy.RECURSIVE`).
- No other field, class, or behavior in `config.py` changes. This is a
  type-tightening edit only — every existing env var name and default value
  stays identical.

---

## 2. Project Structure (authoritative — do not deviate)

```
repo-root/
├── app/
│   ├── main.py
│   ├── config.py                # done
│   ├── models.py                # done
├── routes/
│   ├── health.py
│   ├── search.py
│   └── query.py
├── services/
│   ├── semantic_cache.py
│   ├── conversation.py
│   ├── query_router.py
│   ├── query_decomposer.py
│   ├── document_grader.py
│   └── rag_pipeline.py
├── retrieval/
│   ├── filters.py
│   ├── hybrid_retriever.py
│   └── reranker.py
├── agents/
│   ├── adaptive_router.py
│   └── crag.py
├── tools/
│   ├── vector_search.py
│   ├── web_search.py
│   └── code_search.py
├── prompts/
│   ├── __init__.py
│   ├── templates.py
│   └── grading.py
├── security/
│   ├── input_guard.py
│   ├── content_filter.py
│   └── output_guard.py
├── pipeline/
│   ├── extractors/
│   │   ├── text_extractor.py    # done
│   │   ├── pdf_extractor.py
│   │   ├── html_extractor.py
│   │   ├── docx_extractor.py
│   │   └── image_extractor.py
│   ├── preprocessor.py
│   ├── deduplicator.py
│   ├── chunker.py
│   ├── embedder.py
│   ├── indexer.py
│   └── ingest.py
├── Dockerfile                   # done
├── docker-compose.yml
├── docker-compose.prod.yml
├── pyproject.toml
└── README.md
```

All internal imports use absolute paths rooted at the repo root, e.g.
`from app.config import get_settings`, `from pipeline.chunker import Chunker`,
`from retrieval.hybrid_retriever import HybridRetriever`. Never use relative
imports (`from . import ...`) across package boundaries.

---

## 3. Global Engineering Conventions (apply to every file below)

1. **No placeholders.** Every function body must be a complete, working
   implementation — no `# TODO`, no `pass`, no `raise NotImplementedError`
   outside of genuine abstract base methods.
2. **Settings access.** Every module that needs configuration calls
   `get_settings()` from `app.config` — never hardcode a value that already
   exists as a `Settings` field. If a new tunable is needed that doesn't
   exist in `config.py` yet, add it to the appropriate `*Settings` group in
   `config.py` as part of that file's generation rather than hardcoding it.
3. **Optional third-party dependencies** (anything not in the Python
   standard library and not already required by `app.config`/`app.models`)
   must be imported lazily inside `__init__` or the function that needs
   them, wrapped in `try/except ImportError`, raising a clear
   `ImportError` with the `pip install` hint. A module must always be
   *importable* even if an optional dependency is missing — only calling the
   function that needs it should fail.
4. **Error types.** Each file that can fail in a domain-specific way defines
   one exception class named `<Concern>Error` (e.g. `EmbeddingError`,
   `IndexingError`, `SecurityError`, `RetrievalError`) inheriting from
   `Exception`, and raises only that type (wrapping lower-level exceptions
   with `raise X(...) from exc`).
5. **Logging.** Every module sets `logger = logging.getLogger(__name__)` at
   module scope. No `print()`. Respect `ObservabilitySettings.log_level`
   indirectly (i.e. just use the standard `logging` levels correctly —
   `DEBUG` for verbose internals, `INFO` for lifecycle events, `WARNING` for
   recoverable problems, `ERROR` for failures).
6. **Typing.** Full type hints on every public function/method signature.
   Use `from __future__ import annotations` in every file.
7. **Internal vs. API data shapes.** Anything that crosses the HTTP boundary
   uses a model from `app.models` (subclassing `APIModel`). Anything purely
   internal (extractor results, chunking intermediates, BM25 index entries)
   uses a plain `dataclass` defined locally in that file, unless it's
   already defined in `app.models` (e.g. `Chunk`, `DocumentMetadata`,
   `RetrievedChunk`) — reuse those, never redefine a parallel shape.
8. **No circular imports.** Respect the dependency direction implied by the
   structure: `pipeline/` and `retrieval/` never import from `services/`,
   `agents/`, `tools/`, or `routes/`. `services/` may import from
   `pipeline/`, `retrieval/`, `tools/`, `prompts/`, `security/`. `agents/`
   may import from `retrieval/`, `tools/`, `prompts/`. `routes/` may import
   from `services/` and `app.models` only. `app/main.py` imports from
   `routes/` only.
9. **Graceful degradation.** Where the milestone plan calls for it (BM25
   unavailable, web search disabled, cache miss, etc.) the code must
   continue with reduced functionality and a `logger.warning(...)`, never
   raise unless the entire operation is genuinely impossible.
10. **Docstrings.** Every module starts with a triple-quoted docstring
    stating its path, purpose, and how it fits into the pipeline — matching
    the style already established in the completed files.

---

## 4. Symbol Contract Table

This is the part that prevents wiring blunders. When generating file *X*,
the listed symbols from its dependencies **must** exist with **exactly**
these names and signatures, and file *X* itself **must** export the symbols
listed in its own row for the files below it to consume.

| File | Must import (exact names) | Must export (exact names) |
|---|---|---|
| `pipeline/extractors/pdf_extractor.py` | `BaseExtractor, ExtractionResult, ExtractionError` from `pipeline.extractors.text_extractor`; `DocumentMetadata` from `app.models` | `PdfExtractor(BaseExtractor)` |
| `pipeline/extractors/html_extractor.py` | same as above + `DEFAULT_ENCODING_FALLBACKS` from `text_extractor` | `HtmlExtractor(BaseExtractor)` |
| `pipeline/extractors/docx_extractor.py` | same base imports | `DocxExtractor(BaseExtractor)` |
| `pipeline/extractors/image_extractor.py` | same base imports | `ImageExtractor(BaseExtractor)` |
| `pipeline/preprocessor.py` | none from this project (stdlib only) | `Preprocessor`, `PreprocessResult` (fields: `text: str`, `removed_boilerplate_lines: list[str]`, `warnings: list[str]`); method `Preprocessor().process(text: str) -> PreprocessResult` |
| `pipeline/deduplicator.py` | none from this project | `Deduplicator`, `DedupResult` (fields: `kept`, `exact_duplicates`, `near_duplicates`); method `Deduplicator().deduplicate(items, text_fn) -> DedupResult`; **must also export** a public function `compute_content_hash(text: str) -> str` (used by `ingest.py` for the idempotency manifest — do not leave this as a private `_sha256` only) |
| `pipeline/chunker.py` | `ChunkingStrategy, get_settings` from `app.config`; `Chunk` from `app.models` | `Chunker` with method `chunk_document(text: str, document_id: str, source_type: str \| None = None) -> list[Chunk]`; also export `BaseChunker, RecursiveChunker, MarkdownChunker, ASTChunker, SemanticChunker` |
| `pipeline/embedder.py` | `EmbeddingProvider, EmbeddingSettings, get_settings` from `app.config`; `Chunk` from `app.models` | `Embedder` with methods `embed_chunks(chunks: list[Chunk]) -> list[Chunk]` (mutates `.embedding` in place) and `embed_texts(texts: Sequence[str]) -> list[list[float]]`; `EmbeddingError`; `EmbeddingCache` (ABC) with `InMemoryEmbeddingCache`, `RedisEmbeddingCache` |
| `pipeline/indexer.py` | `QdrantSettings, get_settings` from `app.config`; `Chunk` from `app.models` | `Indexer` with `index_chunks(chunks: list[Chunk]) -> int` and `remove_document(document_id: str) -> None`; `QdrantIndexer`; `BM25Index` with `search(query: str, top_k: int) -> list[tuple[str, float]]`, `save(path)`, `load(path) -> BM25Index` (classmethod); `IndexingError`. **`BM25Index` must be reusable standalone by `retrieval/hybrid_retriever.py`** — it cannot be a private inner class of `Indexer`. |
| `pipeline/ingest.py` | everything above in `pipeline/*` and `pipeline/extractors/*`; `get_settings` from `app.config` | `IngestionPipeline` with `ingest_path(path, glob="**/*", force=False) -> IngestionReport`; `IngestionReport`, `FileIngestResult`, `IngestionManifest` |
| `retrieval/filters.py` | `MetadataFilter` from `app.models` | function `build_qdrant_filter(filters: list[MetadataFilter])` returning a `qdrant_client.http.models.Filter \| None`; must lazily import `qdrant_client` the same way `pipeline/indexer.py` does |
| `retrieval/hybrid_retriever.py` | `QdrantIndexer, BM25Index` from `pipeline.indexer`; `Embedder` from `pipeline.embedder`; `build_qdrant_filter` from `retrieval.filters`; `RetrievalSettings, get_settings` from `app.config`; `RetrievedChunk, MetadataFilter, RetrievalSource` from `app.models` | `HybridRetriever` with `retrieve(query: str, top_k: int \| None = None, filters: list[MetadataFilter] \| None = None) -> list[RetrievedChunk]`. Internally: embed query via `Embedder.embed_texts([query])[0]`, dense search via `QdrantIndexer`, sparse search via `BM25Index.search`, fuse with Reciprocal Rank Fusion using `RetrievalSettings.rrf_k`, return `top_k_dense ∪ top_k_sparse` fused down to `top_k_final` unless caller overrides `top_k` |
| `retrieval/reranker.py` | `RetrievalSettings, get_settings` from `app.config`; `RetrievedChunk` from `app.models` | `Reranker` with `rerank(query: str, chunks: list[RetrievedChunk], top_n: int \| None = None) -> list[RetrievedChunk]`, setting `.rerank_score` on each chunk; lazily imports a cross-encoder library (`sentence-transformers`' `CrossEncoder`) keyed off `RetrievalSettings.rerank_model` |
| `prompts/templates.py` | none from this project | module-level functions: `render_system_prompt() -> str`, `render_qa_prompt(query: str, context: str) -> str`, `render_rag_prompt(query: str, context: str, citations_required: bool = True) -> str`, `render_summarization_prompt(text: str) -> str`, `render_query_rewrite_prompt(query: str, history: str) -> str`, `render_judge_prompt(question: str, answer: str, context: str) -> str` |
| `prompts/grading.py` | none from this project | `render_relevance_grading_prompt(query: str, chunk_text: str) -> str` returning a prompt whose expected LLM output is parseable into `RelevanceGrade` (from `app.models`) plus a 0–1 score; also export `parse_grading_response(raw: str) -> tuple[RelevanceGrade, float]` |
| `prompts/__init__.py` | `templates`, `grading` (this package's own modules) | re-exports: `from prompts.templates import *` style surface so `from prompts import render_rag_prompt` works directly |
| `security/input_guard.py` | `SecuritySettings, get_settings` from `app.config`; `QueryRequest` from `app.models` | `InputGuard` with `validate(request: QueryRequest) -> None` (raises `SecurityError` on violation); covers prompt-injection heuristic scoring against `prompt_injection_threshold`, PII pattern detection (toggle via `pii_detection_enabled`), length check against `max_query_length`; `SecurityError` |
| `security/content_filter.py` | `SecuritySettings, get_settings` from `app.config` | `ContentFilter` with `check(text: str) -> ContentFilterResult` (dataclass: `is_safe: bool, categories: list[str], reason: str \| None`) |
| `security/output_guard.py` | `Citation` from `app.models`; `SecuritySettings, get_settings` from `app.config` | `OutputGuard` with `verify(answer: str, citations: list[Citation]) -> OutputGuardResult` (dataclass: `is_valid: bool, unverified_claims: list[str], warnings: list[str]`) — checks every citation's `chunk_id`/`document_id` is non-empty and `score` is plausible, and flags sentences in `answer` with no supporting citation when `citations_required` semantics apply |
| `tools/vector_search.py` | `HybridRetriever` from `retrieval.hybrid_retriever`; `RetrievedChunk, MetadataFilter` from `app.models` | `VectorSearchTool` with `search(query: str, top_k: int = 10, filters: list[MetadataFilter] \| None = None) -> list[RetrievedChunk]` — thin pass-through to `HybridRetriever.retrieve` |
| `tools/web_search.py` | `Settings, get_settings` from `app.config` (uses `serper_api_key`/`tavily_api_key`) | `WebSearchTool` with `search(query: str, top_k: int = 5) -> list[dict]` (each dict: `title, url, snippet`); lazily imports `httpx` for the HTTP call; raises `WebSearchError` on total failure, returns `[]` with a logged warning if the API key is unset (graceful degradation, not a hard failure) |
| `tools/code_search.py` | none from this project beyond stdlib `ast`, `pathlib` | `CodeSearchTool` with `search(query: str, repo_path: str, top_k: int = 10) -> list[dict]` (each dict: `file_path, symbol_name, symbol_type, snippet, line_number`); supports symbol-name substring search and AST-based function/class enumeration across `*.py` files under `repo_path` |
| `services/semantic_cache.py` | `RedisSettings, get_settings` from `app.config`; `Embedder` from `pipeline.embedder`; `ChatResponse` from `app.models` | `SemanticCache` with `get(query: str) -> ChatResponse \| None` and `set(query: str, response: ChatResponse) -> None`; lazily imports `redis`; uses `cache_similarity_threshold`/`cache_ttl_seconds`/`cache_key_prefix` from `RedisSettings` |
| `services/conversation.py` | `ConversationSettings, RedisSettings, get_settings` from `app.config`; `ChatMessage` from `app.models` | `ConversationStore` with `add_message(session_id: str, message: ChatMessage) -> None`, `get_history(session_id: str) -> list[ChatMessage]`, `summarize_if_needed(session_id: str) -> None`; lazily imports `redis` |
| `services/query_router.py` | `QueryIntent, ChatMessage` from `app.models` | `QueryRouter` with `route(query: str, history: list[ChatMessage] \| None = None) -> QueryIntent` |
| `services/query_decomposer.py` | `LLMSettings, get_settings` from `app.config`; `render_query_rewrite_prompt` is **not** used here — decomposition uses its own prompt logic inline or via a new `render_decomposition_prompt` added to `prompts/templates.py` (add it there if not already present) | `QueryDecomposer` with `decompose(query: str) -> list[str]` (returns `[query]` unchanged for simple queries, multiple subqueries for compound ones, gated by `FeatureFlags.enable_query_decomposition`) |
| `services/document_grader.py` | `RelevanceGrade` from `app.models`; `render_relevance_grading_prompt, parse_grading_response` from `prompts.grading`; `CragSettings, get_settings` from `app.config` | `DocumentGrader` with `grade(query: str, chunks: list[RetrievedChunk]) -> list[tuple[RetrievedChunk, RelevanceGrade, float]]` |
| `agents/adaptive_router.py` | `QueryIntent` from `app.models` | `AdaptiveRouter` with `decide_route(intent: QueryIntent, grades: list[tuple] \| None = None) -> str` returning one of `"local_rag", "web", "hybrid", "tool", "agent"` |
| `agents/crag.py` | `DocumentGrader` from `services.document_grader`; `WebSearchTool` from `tools.web_search`; `CodeSearchTool` from `tools.code_search`; `RelevanceGrade, RetrievedChunk` from `app.models`; `CragSettings, get_settings` from `app.config` | `CragAgent` with `correct(query: str, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]` implementing the grade → (if bad) web/code search → retry loop bounded by `max_correction_retries` |
| `services/rag_pipeline.py` | **all of**: `ConversationStore` (services.conversation), `QueryRouter` (services.query_router), `QueryDecomposer` (services.query_decomposer), `HybridRetriever` (retrieval.hybrid_retriever), `Reranker` (retrieval.reranker), `DocumentGrader` (services.document_grader), `CragAgent` (agents.crag), `SemanticCache` (services.semantic_cache), `InputGuard` (security.input_guard), `OutputGuard` (security.output_guard), `render_rag_prompt` (prompts), `LLMSettings, get_settings` (app.config), `QueryRequest, ChatResponse, StreamChunk, Citation, ResponseMetadata` (app.models) | `RAGPipeline` with `run(request: QueryRequest) -> ChatResponse` (non-streaming) and `stream(request: QueryRequest) -> AsyncIterator[StreamChunk]` (streaming) — **these two exact method names/signatures are what `routes/query.py` calls; do not rename** |
| `routes/health.py` | `HealthResponse, ComponentHealth, HealthStatus` from `app.models`; `get_settings` from `app.config`; lazily checks Redis/Qdrant connectivity | FastAPI `router = APIRouter()` with `GET /health`, `GET /ready`, `GET /live` |
| `routes/search.py` | `SearchRequest, SearchResponse, SearchResult` from `app.models`; `HybridRetriever` (retrieval.hybrid_retriever); `Reranker` (retrieval.reranker) | FastAPI `router = APIRouter()` with `POST /search` (mounted under `/api` prefix by `main.py`, so the full path is `POST /api/search`) |
| `routes/query.py` | `QueryRequest, ChatResponse, StreamChunk, ErrorResponse` from `app.models`; `RAGPipeline` from `services.rag_pipeline` | FastAPI `router = APIRouter()` with `POST /query` (full path `/api/query`); when `request.stream` is true, returns a `StreamingResponse` iterating `RAGPipeline.stream(request)` and writing `chunk.to_sse()` per the method already defined on `StreamChunk` in `app.models`; otherwise returns `RAGPipeline.run(request)` directly as the response model |
| `app/main.py` | `get_settings` from `app.config`; `health.router, search.router, query.router` from `routes.*`; `ErrorResponse, ErrorDetail` from `app.models` | FastAPI app factory `create_app() -> FastAPI` and module-level `app = create_app()`; registers all three routers under `settings.api_v1_prefix` (`/api`) except health, which is mounted at root (`/health`, `/ready`, `/live` — not `/api/health`); lifespan startup/shutdown logging; global exception handler converting unhandled exceptions to `ErrorResponse`; CORS middleware using `settings.security.allowed_origins` |

---

## 5. Per-File Generation Briefs

> Pull the responsibilities for each file from the original milestone
> roadmap already discussed in this conversation (Milestones 1–9). The
> table in §4 is the binding contract; the bullet points below are the
> *behavior* requirements layered on top of that contract. Generate files
> in this exact order — each depends only on files above it in this list
> (plus the already-done files in §0).

### Pipeline (offline ingestion)
1. **`pipeline/extractors/pdf_extractor.py`** — text via `pypdf`; OCR
   fallback via `pdf2image` + `pytesseract` for pages with little/no
   extractable text; tables via `pdfplumber`; title/author/page-count
   metadata from PDF info dict. All three OCR/table libraries optional.
2. **`pipeline/extractors/html_extractor.py`** — DOM parse via
   `BeautifulSoup`; strip script/style/nav/header/footer/aside/form before
   text extraction; prefer `trafilatura` for boilerplate removal if
   installed, else a BeautifulSoup heuristic; pull title/description/
   author/og-tags/canonical-url/lang into metadata; extract `<table>`s.
3. **`pipeline/extractors/docx_extractor.py`** — paragraphs (headings
   rendered as markdown `#` prefixes by style name), tables, headers/
   footers, embedded images (as raw bytes), and core-properties metadata
   via `python-docx`.
4. **`pipeline/extractors/image_extractor.py`** — OCR via `pytesseract`
   with word-level bounding boxes/confidence via `image_to_data`; flag low
   average confidence in metadata; dimensions/mode in metadata.
5. **`pipeline/preprocessor.py`** — HTML-entity unescape, residual-tag
   strip, Unicode NFKC normalization, control-char strip, repeated-line
   (running header/footer) removal via a configurable repeat threshold,
   whitespace collapse.
6. **`pipeline/deduplicator.py`** — exact dedup via SHA-256 of normalized
   text; near-dup via a pure-Python 64-bit SimHash + Hamming-distance
   threshold (no extra dependency); remember to export
   `compute_content_hash` publicly (§4).
7. **`pipeline/chunker.py`** — four strategies (`RecursiveChunker`,
   `MarkdownChunker`, `ASTChunker`, `SemanticChunker`), all subclassing one
   `BaseChunker`, selected by the `Chunker` facade off
   `ChunkingSettings.strategy` or `source_type`; `chunk_overlap` enforced
   smaller than `chunk_size`; approximate token counting by default with an
   optional `tiktoken`-backed exact counter.
8. **`pipeline/embedder.py`** — provider backends for OpenAI, HuggingFace
   (`sentence-transformers`), Cohere selected off `EmbeddingSettings.provider`;
   batches at `EmbeddingSettings.batch_size`; exponential-backoff retry up
   to `max_retries`; pluggable cache (`InMemoryEmbeddingCache` default,
   `RedisEmbeddingCache` available) keyed by SHA-256 of `(model_name, text)`.
9. **`pipeline/indexer.py`** — `QdrantIndexer` ensures the collection exists
   with `vector_size`/`distance_metric`/HNSW params from `QdrantSettings`
   then upserts; `BM25Index` is a self-contained Okapi BM25 implementation
   (no third-party BM25 dependency) persisted via `pickle` to
   `QdrantSettings.bm25_index_path`; `Indexer` facade keeps both in sync and
   persists BM25 after every write.
10. **`pipeline/ingest.py`** — `IngestionPipeline` dispatches each input
    file to the first extractor whose `supports()` matches (built-in
    registry instantiates every extractor, skipping any with a missing
    optional dependency, with a warning rather than crashing); runs
    Extract → Clean → Dedup → Chunk → Embed → Index per file; tracks a
    persisted content-hash manifest (`IngestionManifest`) so re-ingesting an
    unchanged file is a no-op; one file's failure is caught and recorded,
    never aborts the batch.

### Retrieval
11. **`retrieval/filters.py`** — translates `app.models.MetadataFilter`
    (field/operator/value) into a Qdrant `Filter`/`FieldCondition` tree;
    supports all operators already defined on `MetadataFilter`
    (`eq, ne, gt, gte, lt, lte, in, not_in, contains`).
12. **`retrieval/hybrid_retriever.py`** — dense search via `QdrantIndexer`
    (top `RetrievalSettings.top_k_dense`), sparse search via `BM25Index`
    (top `top_k_sparse`), fused via Reciprocal Rank Fusion using `rrf_k` and
    `hybrid_alpha`, metadata filters applied to the dense leg via
    `build_qdrant_filter`, final list truncated to `top_k_final`.
13. **`retrieval/reranker.py`** — cross-encoder rerank gated by
    `RetrievalSettings.rerank_enabled`; sets `.rerank_score`; truncates to
    `rerank_top_n`; no-ops (returns input unchanged) when reranking is
    disabled or the cross-encoder dependency is missing.

### Prompts
14. **`prompts/templates.py`** — see exact function list in §4; also add
    `render_decomposition_prompt(query: str) -> str` here since
    `query_decomposer.py` needs it.
15. **`prompts/grading.py`** — grading prompt + response parser, output
    must map cleanly onto `RelevanceGrade` plus a numeric 0–1 score for
    `CragSettings` threshold comparisons.
16. **`prompts/__init__.py`** — flat re-export surface only, no new logic.

### Security
17. **`security/input_guard.py`** — prompt-injection heuristic (pattern/
    keyword scoring against `prompt_injection_threshold`), basic PII regex
    detection (emails, phone numbers, SSNorth-American-style numbers, credit
    cards), `max_query_length` enforcement.
18. **`security/content_filter.py`** — keyword/category-based output
    moderation check returning safe/unsafe + matched categories.
19. **`security/output_guard.py`** — citation completeness/plausibility
    check; flags answer sentences with no backing citation.

### Tools
20. **`tools/vector_search.py`** — pass-through wrapper over
    `HybridRetriever`.
21. **`tools/web_search.py`** — real HTTP call (lazy `httpx` import) to
    whichever of `serper_api_key`/`tavily_api_key` is configured; returns
    `[]` with a warning (not an exception) if no key is set.
22. **`tools/code_search.py`** — pure stdlib (`ast` + `pathlib`) symbol/
    file/substring search across a repo path.

### Services
23. **`services/semantic_cache.py`** — Redis-backed; looks up by embedding
    cosine similarity ≥ `cache_similarity_threshold`, not exact string match.
24. **`services/conversation.py`** — Redis-backed sliding window of
    `max_history_turns`/`max_history_tokens`; triggers summarization at
    `summarization_trigger_turns` when `summarization_enabled`.
25. **`services/query_router.py`** — lightweight intent classifier (rule-
    based heuristics are acceptable; LLM-based classification is also
    acceptable as long as the signature in §4 is honored).
26. **`services/query_decomposer.py`** — gated by
    `FeatureFlags.enable_query_decomposition`; no-ops to `[query]` when the
    flag is off or the query doesn't look compound.
27. **`services/document_grader.py`** — produces a `(chunk, grade, score)`
    triple per retrieved chunk using the grading prompt from
    `prompts/grading.py`.
28. **`services/rag_pipeline.py`** — the master orchestrator; must
    implement the exact pipeline order already specified in Milestone 3
    (history → router → decomposer → retriever → reranker → CRAG →
    context builder → LLM → streaming → save history → return answer);
    must call `InputGuard.validate` before retrieval and `OutputGuard.verify`
    before returning; must check `SemanticCache` before retrieval and
    populate it after generation when `use_cache` is true.

### Agents
29. **`agents/adaptive_router.py`** — pure decision function, no I/O.
30. **`agents/crag.py`** — implements the grade → correct loop bounded by
    `max_correction_retries`; calls `WebSearchTool`/`CodeSearchTool` only
    when `web_search_fallback`/`code_search_fallback` are enabled.

### API layer
31. **`routes/health.py`** — every check (Redis, Qdrant, embedding,
    LLM) wrapped so one failing dependency degrades overall status to
    `DEGRADED`/`UNHEALTHY` per `HealthResponse`'s own status-derivation
    logic, never raises an unhandled exception out of the endpoint.
32. **`routes/search.py`** — retrieval + optional rerank only, no LLM call,
    returns latency in `SearchResponse.latency_ms`.
33. **`routes/query.py`** — dispatches to `RAGPipeline.run` or
    `RAGPipeline.stream` based on `request.stream`; streaming path sets
    `media_type="text/event-stream"`.

### Runtime
34. **`app/main.py`** — wires everything; **no business logic lives here**
    (per the original constraint already stated in the milestone plan).

### Infrastructure
35. **`docker-compose.yml`** — dev stack: this service + Redis + Qdrant,
    env vars sourced from `.env`, named volumes for Qdrant storage and the
    BM25 index path, depends_on with healthchecks.
36. **`docker-compose.prod.yml`** — overlay/extension of the dev compose
    file: GPU reservation block, healthchecks, `restart: unless-stopped`,
    persistent named volumes, resource limits.
37. **`pyproject.toml`** — **must list only packages actually imported by
    the generated code** (no speculative LangChain/LangGraph dependency
    unless a generated file truly imports them — none of the files in this
    spec do). Core: `fastapi`, `uvicorn`, `pydantic`, `pydantic-settings`,
    `redis`, `qdrant-client`. Optional/extras groups for: `openai`,
    `sentence-transformers`, `cohere`, `pypdf`, `pdfplumber`, `pdf2image`,
    `pytesseract`, `Pillow`, `beautifulsoup4`, `lxml`, `trafilatura`,
    `python-docx`, `tiktoken`, `httpx`, `structlog`, `prometheus-client`,
    `opentelemetry-sdk`, `opentelemetry-exporter-otlp`.
38. **`README.md`** — must document every env var from every `*Settings`
    class in `app/config.py` (group by section), the three API endpoints
    and their request/response shapes from `app/models.py`, local dev
    setup via `docker-compose.yml`, production deployment via
    `docker-compose.prod.yml` + the `Dockerfile`, and a troubleshooting
    section covering each optional-dependency `ImportError` message defined
    across the extractor/embedder/reranker files.

---

## 6. Final Integration Checklist (verify before declaring any file "done")

- [ ] Every import in the new file resolves to a symbol that the producing
      file actually exports per §4 — no guessed names.
- [ ] No file imports from a layer below it per the dependency direction in
      §3 rule 8.
- [ ] Every `Settings`/`*Settings` field referenced actually exists in the
      patched `app/config.py` (§1) — if not, add it there first.
- [ ] Every `app.models` shape referenced (`Chunk`, `DocumentMetadata`,
      `RetrievedChunk`, `QueryRequest`, `ChatResponse`, `StreamChunk`,
      `Citation`, `MetadataFilter`, enums) is reused as-is, never
      redefined locally.
- [ ] `RAGPipeline.run` / `RAGPipeline.stream` signatures match exactly
      what `routes/query.py` calls — this is the single most important
      contract in the whole system.
- [ ] `BM25Index` is shared (same `bm25_index_path`) between
      `pipeline/indexer.py` (writer) and `retrieval/hybrid_retriever.py`
      (reader) — both must resolve the path from
      `get_settings().qdrant.bm25_index_path`, never a literal string.
- [ ] Optional-dependency `ImportError` messages are consistent with what
      `pyproject.toml`'s extras groups (§5, item 37) actually install.
