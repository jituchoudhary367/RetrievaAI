# Full-Stack Real-Time Wiring — Implementation Plan

Wire the existing 7-page frontend to a **real, persistent, zero-mock-data backend** per the prompt's §0–§6 contract. The current backend has: FastAPI routes (`/query`, `/search`, `/health`, `/ingest`), Redis-backed conversation store, Qdrant+BM25 hybrid retrieval, CRAG agent, 3 tools (`vector_search`, `web_search`, `code_search`), and an in-process blocking ingestion pipeline. **No Postgres, no telemetry tables, no job queue, no blob storage, no user/tenant model, no auth** currently exist.

---

## User Review Required

> [!IMPORTANT]
> **Postgres is a new infrastructure dependency.** The current stack is Redis + Qdrant only. This plan adds PostgreSQL for all persistent relational data (telemetry, documents, settings, users, audit logs, etc.). This requires adding `postgres` to `docker-compose.yml` and `asyncpg`/`SQLAlchemy` to `pyproject.toml`.

> [!IMPORTANT]
> **Auth/RBAC/Multi-tenancy are referenced by the spec but have no existing code.** The prompt references `MULTI_TENANCY_AMENDMENT.md`, `RBAC_AMENDMENT.md`, `AUTH_AMENDMENT.md`, and `EMAIL_VERIFICATION_PASSWORD_RESET_AMENDMENT.md` as prior contracts. **I don't have those documents in the repo.** I will implement the auth/user/tenant models and JWT middleware as described in the wiring prompt itself (§1.8, §1.10, §2), but without access to the full amendment specs, some design decisions (e.g., exact RBAC permission names, invitation flow details, email transport configuration) will be based on the wiring prompt's references. **Please confirm this is acceptable, or provide the amendment documents.**

> [!WARNING]
> **Scope is massive (~50+ new files, 15+ modified files).** I recommend implementing in **6 phased batches** (see below), each independently testable. Each phase builds on the previous. Do you want me to execute all 6 phases, or start with a subset?

## Open Questions

> [!IMPORTANT]
> 1. **Amendment documents**: Are `MULTI_TENANCY_AMENDMENT.md`, `RBAC_AMENDMENT.md`, `AUTH_AMENDMENT.md`, `EMAIL_VERIFICATION_PASSWORD_RESET_AMENDMENT.md` available somewhere in or near the repo? If so, please share their paths. If not, I'll implement auth based on the wiring prompt's §1.8/§1.10/§2 references.
> 2. **Database migrations**: Should I use Alembic for schema migrations, or generate raw SQL `CREATE TABLE` scripts?  
> 3. **Frontend mock data removal**: The existing frontend pages (analytics, documents, tools, settings, ingestion) presumably use hardcoded/mock data today. Should I systematically search and replace all mock data, or focus on the backend first and wire frontend in a follow-up?

---

## Proposed Changes

The implementation is organized into **6 phases**, each producing independently runnable/testable code.

---

### Phase 1: Database Foundation & ORM Models

Add PostgreSQL, SQLAlchemy async, and Alembic. Define all new database tables.

#### [NEW] [db/](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/db/) — Database package
- `__init__.py` — Package init
- `engine.py` — `async_engine`, `async_session_factory`, `get_db()` dependency
- `base.py` — `Base = declarative_base()` with `tenant_id` mixin

#### [NEW] [db/models/](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/db/models/) — SQLAlchemy ORM models

| File | Tables | Source (§) |
|---|---|---|
| `user.py` | `User`, `UserSession` | §1.8, §1.10 |
| `tenant.py` | `Tenant`, `TenantConfig` | Referenced from amendments |
| `telemetry.py` | `QueryEvent`, `QueryEventCitation`, `SearchEvent`, `SearchClickEvent` | §1.1 |
| `ingestion.py` | `IngestionJob`, `IngestionJobLog` | §1.2 |
| `document.py` | `Document` | §1.3 |
| `tool.py` | `Tool`, `ToolExecution` | §1.5 |
| `eval.py` | `EvalQuery`, `EvalRun` | §1.6 |
| `settings.py` | `RuntimeSetting` | §1.7 |
| `security.py` | `ApiKey` | §1.8 |
| `audit.py` | `AuditLogEntry`, `Notification` | §1.9 |
| `conversation.py` | `Conversation`, `ConversationMessage` | §1.10 |
| `health.py` | `HealthSample` | §2 (system-health) |

#### [NEW] [db/migrations/](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/db/migrations/) — Alembic migration scripts
- `alembic.ini`, `env.py`, initial migration with all tables

#### [MODIFY] [pyproject.toml](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/pyproject.toml)
Add: `sqlalchemy[asyncio]`, `asyncpg`, `alembic`, `rq`, `pyotp`, `qrcode`, `python-multipart`

#### [MODIFY] [config.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/app/config.py)
Add `DatabaseSettings` (postgres host/port/db/user/password/pool_size) and `BlobStorageSettings` (root_path, backend type) sub-settings groups.

#### [MODIFY] [docker-compose.yml](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/docker-compose.yml)
Add `postgres` service, add `worker` service (same image, `command: rq worker ingestion`), add `postgres_data` volume.

#### [MODIFY] [docker-compose.prod.yml](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/docker-compose.prod.yml)
Add `postgres` and `worker` with production resource limits.

---

### Phase 2: Auth, Users, Security Middleware

#### [NEW] [security/auth.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/security/auth.py)
JWT token creation/validation, `get_current_user()` FastAPI dependency, `require_role()` dependency factory for RBAC.

#### [NEW] [routes/auth.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/routes/auth.py)
Endpoints:
- `POST /api/auth/register`, `POST /api/auth/login`, `POST /api/auth/refresh`
- `GET /api/auth/me` → `UserProfile{email, tenantId, tenantName, roles}` (§1.10)
- `GET /api/auth/users` (admin-only, `TENANT_ADMIN`) — lists tenant's users
- `POST /api/auth/2fa/enable`, `POST /api/auth/2fa/verify`, `POST /api/auth/2fa/disable` (§1.8)

#### [MODIFY] [app/main.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/app/main.py)
Register auth router, add DB lifecycle (create tables on startup), register new route modules.

---

### Phase 3: Core Backend Subsystems

#### [NEW] [services/blob_storage.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/services/blob_storage.py)
`save(file) -> path`, `load(path) -> bytes`, `delete(path)` — local filesystem backed (§1.4).

#### [NEW] [services/telemetry.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/services/telemetry.py)
Fire-and-forget `record_query_event()`, `record_search_event()`, `record_search_click()` — writes to Postgres asynchronously (§1.1).

#### [NEW] [services/runtime_settings.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/services/runtime_settings.py)
`get_effective(tenant_id, key, default)` (TTL-cached), `set(tenant_id, key, value)` (§1.7).

#### [NEW] [services/audit.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/services/audit.py)
`log_action(tenant_id, user_id, action, target)` — writes `AuditLogEntry` (§1.9).

#### [NEW] [services/notification.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/services/notification.py)
`create_notification()`, `get_notifications()`, `mark_read()` (§1.9).

#### [NEW] [services/eval_service.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/services/eval_service.py)
Replays `EvalQuery` set through `HybridRetriever`, computes MRR/HitRate@5/NDCG@10/Top-1 Accuracy, stores `EvalRun` (§1.6).

#### [NEW] [services/health_sampler.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/services/health_sampler.py)
Periodic sampler that writes `HealthSample` rows (CPU, memory, component latencies) for the Analytics system-health panel.

#### [NEW] [tasks/ingestion_tasks.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/tasks/ingestion_tasks.py)
RQ task wrapper around `IngestionPipeline` — persists `IngestionJob`/`IngestionJobLog` rows, publishes to Redis Pub/Sub `ingestion:{job_id}` (§1.2).

#### [NEW] [tasks/__init__.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/tasks/__init__.py)

#### [MODIFY] [services/rag_pipeline.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/services/rag_pipeline.py)
- After `run()`/`stream()` responds, fire-and-forget write a `QueryEvent` + `QueryEventCitation` rows via `telemetry.record_query_event()`.
- Accept `model_override`, `retrieval_mode`, `force_web_search` from the expanded `QueryRequest` (§1.10).
- Add `retrieved_count`, `reranked_count`, `top_k` to `ResponseMetadata`.
- Write-through conversation messages to Postgres `ConversationMessage` alongside Redis.

#### [MODIFY] [services/conversation.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/services/conversation.py)
Add write-through to Postgres `Conversation`/`ConversationMessage` tables on every `add_message()`.

#### [MODIFY] [app/models.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/app/models.py)
- Add `model_override`, `retrieval_mode`, `force_web_search` to `QueryRequest`.
- Add `retrieved_count`, `reranked_count`, `top_k` to `ResponseMetadata`.

#### [MODIFY] [retrieval/hybrid_retriever.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/retrieval/hybrid_retriever.py)
Accept `retrieval_mode` parameter to skip BM25 or dense leg per request.

#### [MODIFY] [pipeline/ingest.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/pipeline/ingest.py)
At indexing time, also write/update a `Document` row in Postgres (§1.3) and save the original file via `blob_storage.save()` (§1.4).

---

### Phase 4: New API Routes

#### [NEW] [routes/documents.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/routes/documents.py)
`GET /api/documents`, `GET /api/documents/{id}`, `DELETE /api/documents/{id}`, `GET /api/documents/{id}/chunks`, `GET /api/documents/{id}/download`

#### [NEW] [routes/ingestion.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/routes/ingestion.py)
`GET /api/ingestion/jobs`, `POST /api/ingestion/jobs`, `GET /api/ingestion/jobs/{id}`, `DELETE /api/ingestion/jobs/{id}`, `GET /api/ingestion/jobs/{id}/stream` (SSE), `POST /api/ingestion/jobs/{id}/cancel`

#### [NEW] [routes/analytics.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/routes/analytics.py)
`GET /api/analytics/overview`, `/query-distribution`, `/top-queries`, `/top-sources`, `/user-engagement`, `/retrieval-quality`, `/cost-breakdown`, `/system-health`

#### [NEW] [routes/tools.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/routes/tools.py)
`GET /api/tools`, `POST /api/tools`, `GET /api/tools/{id}`, `GET /api/tools/{id}/executions`, `POST /api/tools/{id}/test`

#### [NEW] [routes/settings.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/routes/settings.py)
`GET/PUT /api/settings/{category}`, `/api-keys`, `/sessions`, `/audit-log`, `/export`, `/reset`, `/delete-system`

#### [NEW] [routes/conversations.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/routes/conversations.py)
`GET /api/conversations`, `GET /api/conversations/{id}/messages`

#### [NEW] [routes/notifications.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/routes/notifications.py)
`GET /api/notifications`, `POST /api/notifications/{id}/read`

#### [MODIFY] [routes/search.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/routes/search.py)
Add `POST /api/search/code`, `POST /api/search/web`, `POST /api/search/events/click`. Add telemetry recording after each search.

#### [MODIFY] [routes/ingest.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/routes/ingest.py)
Refactor: the existing blocking ingest route will be replaced by the new async job-based `routes/ingestion.py`. Keep the old file but deprecate it, or remove it.

#### [MODIFY] [routes/__init__.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/routes/__init__.py)
Export all new routers.

#### [MODIFY] [app/main.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/app/main.py)
Register all new routers with the FastAPI app.

---

### Phase 5: Tool Execution Logging & Seeding

#### [MODIFY] [agents/crag.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/agents/crag.py)
After each web_search/code_search/vector_search invocation, log a `ToolExecution` row.

#### [MODIFY] [tools/web_search.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/tools/web_search.py)
Add execution logging hook.

#### [MODIFY] [tools/code_search.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/tools/code_search.py)
Add execution logging hook.

#### [NEW] [db/seed.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/db/seed.py)
Seeds `Tool` table with 3 tools: `vector_search`, `web_search`, `code_search` (§1.5). Run on first startup.

---

### Phase 6: Frontend Wiring

#### [MODIFY] Frontend API layer — [lib/api/](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/frontend/lib/api/)

New API modules:
| File | Endpoints |
|---|---|
| `auth.ts` | `/api/auth/me`, `/api/auth/login`, `/api/auth/register`, `/api/auth/users`, `/api/auth/2fa/*` |
| `documents.ts` | `/api/documents`, `/api/documents/{id}`, chunks, download |
| `ingestion.ts` | `/api/ingestion/jobs`, SSE stream |
| `analytics.ts` | All `/api/analytics/*` |
| `tools.ts` | `/api/tools`, executions, test |
| `settings.ts` | `/api/settings/*`, api-keys, sessions, audit-log |
| `conversations.ts` | `/api/conversations`, messages |
| `notifications.ts` | `/api/notifications` |

#### [MODIFY] [lib/types/models.ts](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/frontend/lib/types/models.ts)
Add TypeScript types for all new API responses (documents, ingestion jobs, tools, analytics, settings, etc.).

#### [MODIFY] [lib/api/client.ts](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/frontend/lib/api/client.ts)
Add JWT token header injection (Bearer token from localStorage/cookie).

#### [MODIFY] `QueryRequest` type
Add `modelOverride`, `retrievalMode`, `forceWebSearch`.

#### [MODIFY] `ResponseMetadata` type
Add `retrievedCount`, `rerankedCount`, `topK`.

#### Replace mock data in all page components:
- **Chat** (`app/page.tsx`, `components/chat/*`) — wire model/search-type/web-search controls to real `QueryRequest` fields; conversations from `/api/conversations`.
- **Search** (`app/search/page.tsx`, `components/search/*`) — wire tabs to real endpoints; add click tracking.
- **Documents** (`app/documents/page.tsx`, `components/documents/*`) — replace mock table with `GET /api/documents`; wire Preview/Download/Delete.
- **Ingestion** (`app/ingestion/page.tsx`, `components/ingestion/*`) — replace mock with `GET/POST /api/ingestion/jobs`; SSE for live logs.
- **Analytics** (`app/analytics/page.tsx`, `components/analytics/*`) — replace all hardcoded charts/stats with `/api/analytics/*`.
- **Tools** (`app/tools/page.tsx`, `components/tools/*`) — replace mock with `GET /api/tools`; wire Create/Test.
- **Settings** (`app/settings/page.tsx`, `components/settings/*`) — wire all tabs to real endpoints.
- **Layout** (`components/layout/*`) — wire notification bell, avatar, conversation sidebar.

---

## Verification Plan

### Automated Tests
```bash
# Backend: Run from backend/ directory
pytest tests/ -v --cov=. --cov-report=term-missing

# Frontend: Type checking
cd frontend && npx tsc --noEmit

# Docker: Full stack smoke test
docker compose up --build -d
curl -f http://localhost:8000/health/ready
curl -f http://localhost:8000/api/auth/me  # (expect 401 without token)
docker compose down
```

### Manual Verification
- **Integration checklist**: Walk through every item in §6 of the wiring prompt.
- **Zero-mock audit**: Grep frontend for hardcoded data arrays, confirm each is replaced with an API call per §5.
- **SSE streaming**: Test ingestion job live logs by uploading a file and watching the stream.
- **Conversation persistence**: Create a conversation, flush Redis, verify conversations still load from Postgres.
