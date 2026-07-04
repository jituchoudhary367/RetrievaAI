# RAG Application File Map

This document maps the repository structure and explains what each meaningful file or directory does. It includes source files, config, entrypoints, runtime storage, and generated artifacts. For very large runtime folders, the role is described at the directory level so the map stays readable while still covering the whole project.

## Root

- [implementation_plan.md](implementation_plan.md) - High-level implementation roadmap for the expanded full-stack RAG system. It describes the target architecture, phased backend/frontend work, API contracts, persistence model, and verification plan.
- [implementation_plan1](implementation_plan1) - Additional planning artifact. It appears to be a companion or alternate plan file and should be treated as a design reference rather than runtime code.
- [start_all.bat](start_all.bat) - Windows launcher that starts Qdrant, Redis, the backend API, and the frontend dev server in separate windows.
- [test_doc.txt](test_doc.txt) - General test/documentation note file at the workspace root.
- [snapshots/](snapshots/) - Workspace-level snapshot storage for saved state or exported artifacts.
- [storage/](storage/) - Runtime storage data, including Raft state and collection metadata for the embedded/local services.

## Backend

### Backend Entry and Deployment

- [backend/run.py](backend/run.py) - Local FastAPI entrypoint. Reads configuration and starts Uvicorn with the app factory in `app.main`.
- [backend/Dockerfile](backend/Dockerfile) - Container build for the backend service.
- [backend/docker-compose.yml](backend/docker-compose.yml) - Local multi-service stack definition for API, worker, Redis, Qdrant, and Postgres.
- [backend/docker-compose.prod.yml](backend/docker-compose.prod.yml) - Production override for the backend stack with tighter runtime settings.
- [backend/alembic.ini](backend/alembic.ini) - Alembic migration configuration.
- [backend/migrate_db.py](backend/migrate_db.py) - Database migration helper script.
- [backend/print_routes.py](backend/print_routes.py) - Utility script to inspect or print available backend routes.
- [backend/clear_sessions.py](backend/clear_sessions.py) - Utility script for clearing stored sessions.
- [backend/fix_untitled.py](backend/fix_untitled.py) - Utility script retained for a specific local repair task.

### Backend Package and App Core

- [backend/app/__init__.py](backend/app/__init__.py) - Marks the application package.
- [backend/app/config.py](backend/app/config.py) - Central settings module for Redis, Qdrant, LLM, embeddings, chunking, retrieval, CRAG, email, and database configuration.
- [backend/app/main.py](backend/app/main.py) - FastAPI application factory. Creates tables, seeds data, starts background health sampling, registers routers, and defines global middleware and error handlers.
- [backend/app/models.py](backend/app/models.py) - Shared Pydantic request/response models, enums, and stream chunks used across routes, services, and retrieval code.

### Backend Database Layer

- [backend/db/__init__.py](backend/db/__init__.py) - Database package exports.
- [backend/db/base.py](backend/db/base.py) - SQLAlchemy declarative base plus shared mixins such as timestamps and tenant scoping.
- [backend/db/engine.py](backend/db/engine.py) - Async SQLAlchemy engine, session factory, and DB dependency provider.
- [backend/db/repository.py](backend/db/repository.py) - Minimal async CRUD helpers used by auth and tenant-related flows.
- [backend/db/seed.py](backend/db/seed.py) - Idempotent database seeding for baseline tenant and built-in tools.

#### Backend ORM Models

- [backend/db/models/__init__.py](backend/db/models/__init__.py) - Imports ORM models so SQLAlchemy metadata is fully registered.
- [backend/db/models/user.py](backend/db/models/user.py) - User and user-session persistence.
- [backend/db/models/tool.py](backend/db/models/tool.py) - Tool catalog and tool execution records.
- [backend/db/models/tenant.py](backend/db/models/tenant.py) - Tenant and tenant configuration tables.
- [backend/db/models/telemetry.py](backend/db/models/telemetry.py) - Query/search telemetry tables and search-click records.
- [backend/db/models/settings.py](backend/db/models/settings.py) - Runtime settings table for persisted configuration overrides.
- [backend/db/models/security.py](backend/db/models/security.py) - API key persistence.
- [backend/db/models/audit.py](backend/db/models/audit.py) - Audit log entries and notifications.
- [backend/db/models/ingestion.py](backend/db/models/ingestion.py) - Ingestion job and job-log tracking.
- [backend/db/models/document.py](backend/db/models/document.py) - Document catalog records for indexed content.
- [backend/db/models/conversation.py](backend/db/models/conversation.py) - Conversation and conversation-message persistence.
- [backend/db/models/eval.py](backend/db/models/eval.py) - Offline evaluation query sets and evaluation runs.
- [backend/db/models/health.py](backend/db/models/health.py) - Periodic system health samples.
- [backend/db/models/invite.py](backend/db/models/invite.py) - Team invitation records.
- [backend/db/models/auth_token.py](backend/db/models/auth_token.py) - Verification and password-reset token persistence.

### Backend Routes

- [backend/routes/__init__.py](backend/routes/__init__.py) - Route package export surface.
- [backend/routes/auth.py](backend/routes/auth.py) - Signup, login, invite, verification, password reset, and accept-invite endpoints.
- [backend/routes/oauth.py](backend/routes/oauth.py) - OAuth-related routes and callback handling.
- [backend/routes/query.py](backend/routes/query.py) - Conversational RAG query endpoint and streaming SSE endpoint.
- [backend/routes/search.py](backend/routes/search.py) - Retrieval search endpoints for document, web, code, and click telemetry.
- [backend/routes/health.py](backend/routes/health.py) - Liveness and readiness probes for the service and its dependencies.
- [backend/routes/ingest.py](backend/routes/ingest.py) - Legacy blocking ingestion router kept for backward compatibility.
- [backend/routes/ingestion.py](backend/routes/ingestion.py) - Async ingestion job API.
- [backend/routes/documents.py](backend/routes/documents.py) - Document listing, details, chunks, download, and delete APIs.
- [backend/routes/analytics.py](backend/routes/analytics.py) - Analytics and observability endpoints.
- [backend/routes/tools.py](backend/routes/tools.py) - Tool catalog, execution history, and test endpoints.
- [backend/routes/settings.py](backend/routes/settings.py) - Settings, API keys, sessions, audit log, export, and destructive system actions.
- [backend/routes/conversations.py](backend/routes/conversations.py) - Conversation listing and message retrieval.
- [backend/routes/notifications.py](backend/routes/notifications.py) - Notification listing and read-state updates.

### Backend Services

- [backend/services/__init__.py](backend/services/__init__.py) - Service package export surface.
- [backend/services/auth_service.py](backend/services/auth_service.py) - Signup, login, invite, verification, and password-reset business logic.
- [backend/services/audit.py](backend/services/audit.py) - Audit logging helper for sensitive actions.
- [backend/services/blob_storage.py](backend/services/blob_storage.py) - Local blob/document storage abstraction.
- [backend/services/conversation.py](backend/services/conversation.py) - Redis-backed conversation store with sliding window trimming and summarization.
- [backend/services/document_grader.py](backend/services/document_grader.py) - Document relevance grading logic used by CRAG.
- [backend/services/email_service.py](backend/services/email_service.py) - Email delivery integration.
- [backend/services/email_templates.py](backend/services/email_templates.py) - HTML and text email templates.
- [backend/services/eval_service.py](backend/services/eval_service.py) - Offline retrieval evaluation runner and metric calculator.
- [backend/services/health_sampler.py](backend/services/health_sampler.py) - Background collector for system health metrics.
- [backend/services/notification.py](backend/services/notification.py) - Notification creation and lifecycle helpers.
- [backend/services/query_decomposer.py](backend/services/query_decomposer.py) - Breaks complex questions into subqueries.
- [backend/services/query_router.py](backend/services/query_router.py) - Routes a query to the right intent or processing lane.
- [backend/services/rag_pipeline.py](backend/services/rag_pipeline.py) - Main orchestrator for validation, cache, retrieval, reranking, CRAG, generation, and persistence.
- [backend/services/runtime_settings.py](backend/services/runtime_settings.py) - Runtime configuration retrieval and updates with caching.
- [backend/services/semantic_cache.py](backend/services/semantic_cache.py) - Semantic query cache backed by Redis or fallback storage.
- [backend/services/telemetry.py](backend/services/telemetry.py) - Fire-and-forget persistence of query/search telemetry.
- [backend/services/tool_logger.py](backend/services/tool_logger.py) - Tool execution logging support.
- [backend/services/user_preferences.py](backend/services/user_preferences.py) - Per-user integration/settings preferences storage.
- [backend/services/tenant_registry.py](backend/services/tenant_registry.py) - Tenant lookup and tenant-scoped service helpers.

### Backend Agents

- [backend/agents/__init__.py](backend/agents/__init__.py) - Agent package export surface.
- [backend/agents/adaptive_router.py](backend/agents/adaptive_router.py) - Pure routing decision helper that maps a query intent to a processing target.
- [backend/agents/crag.py](backend/agents/crag.py) - Corrective RAG agent that grades retrieval quality and optionally falls back to web/code search.

### Backend Pipeline

- [backend/pipeline/__init__.py](backend/pipeline/__init__.py) - Pipeline package export surface.
- [backend/pipeline/preprocessor.py](backend/pipeline/preprocessor.py) - Text cleanup and normalization before chunking.
- [backend/pipeline/deduplicator.py](backend/pipeline/deduplicator.py) - Content deduplication and content hashing.
- [backend/pipeline/chunker.py](backend/pipeline/chunker.py) - Splits documents into retrieval chunks.
- [backend/pipeline/embedder.py](backend/pipeline/embedder.py) - Embedding generation for documents and queries.
- [backend/pipeline/indexer.py](backend/pipeline/indexer.py) - Writes dense vectors and sparse BM25 artifacts to the indexing layer.
- [backend/pipeline/ingest.py](backend/pipeline/ingest.py) - End-to-end offline ingestion orchestration from extraction through indexing.

#### Backend Extractors

- [backend/pipeline/extractors/__init__.py](backend/pipeline/extractors/__init__.py) - Extractor package export surface.
- [backend/pipeline/extractors/text_extractor.py](backend/pipeline/extractors/text_extractor.py) - Plain-text extraction.
- [backend/pipeline/extractors/pdf_extractor.py](backend/pipeline/extractors/pdf_extractor.py) - PDF extraction and OCR-related support.
- [backend/pipeline/extractors/html_extractor.py](backend/pipeline/extractors/html_extractor.py) - HTML page extraction and text cleanup.
- [backend/pipeline/extractors/docx_extractor.py](backend/pipeline/extractors/docx_extractor.py) - DOCX document extraction.
- [backend/pipeline/extractors/image_extractor.py](backend/pipeline/extractors/image_extractor.py) - Image OCR and text extraction.

### Backend Retrieval

- [backend/retrieval/__init__.py](backend/retrieval/__init__.py) - Retrieval package export surface.
- [backend/retrieval/filters.py](backend/retrieval/filters.py) - Converts metadata filter objects into Qdrant-compatible filter expressions.
- [backend/retrieval/hybrid_retriever.py](backend/retrieval/hybrid_retriever.py) - Dense + sparse hybrid retriever with reciprocal rank fusion.
- [backend/retrieval/reranker.py](backend/retrieval/reranker.py) - Cross-encoder reranking layer for retrieved chunks.

### Backend Prompts

- [backend/prompts/__init__.py](backend/prompts/__init__.py) - Prompt package export surface.
- [backend/prompts/templates.py](backend/prompts/templates.py) - Prompt templates for system, RAG, and summarization behavior.
- [backend/prompts/grading.py](backend/prompts/grading.py) - Prompt templates for document grading and CRAG support.

### Backend Security

- [backend/security/__init__.py](backend/security/__init__.py) - Security package export surface.
- [backend/security/auth.py](backend/security/auth.py) - JWT creation, validation, and current-user dependency helpers.
- [backend/security/content_filter.py](backend/security/content_filter.py) - Content filtering and safety screening helpers.
- [backend/security/input_guard.py](backend/security/input_guard.py) - Input validation and prompt-injection style guardrails.
- [backend/security/output_guard.py](backend/security/output_guard.py) - Response safety and output verification.
- [backend/security/passwords.py](backend/security/passwords.py) - Password hashing and verification utilities.

### Backend Tools

- [backend/tools/__init__.py](backend/tools/__init__.py) - Tool package export surface.
- [backend/tools/vector_search.py](backend/tools/vector_search.py) - Dense/vector search tool wrapper.
- [backend/tools/web_search.py](backend/tools/web_search.py) - External web-search tool wrapper.
- [backend/tools/code_search.py](backend/tools/code_search.py) - Code search tool wrapper.

### Backend Tasks

- [backend/tasks/__init__.py](backend/tasks/__init__.py) - Task package export surface.
- [backend/tasks/ingestion_tasks.py](backend/tasks/ingestion_tasks.py) - Background ingestion task wrapper, typically for queue/worker execution.

### Backend Data and Migrations

- [backend/alembic/README](backend/alembic/README) - Alembic scaffold documentation.
- [backend/alembic/env.py](backend/alembic/env.py) - Alembic runtime migration environment.
- [backend/alembic/script.py.mako](backend/alembic/script.py.mako) - Template used for new migration files.
- [backend/alembic/versions/](backend/alembic/versions/) - Generated migration revisions.
- [backend/data/ingest_manifest.json](backend/data/ingest_manifest.json) - Idempotency manifest used by ingestion to skip already processed content.
- [backend/data/bm25_index/](backend/data/bm25_index/) - Persisted BM25 sparse-index artifacts.
- [backend/data/blobs/](backend/data/blobs/) - Persisted uploaded/original document blobs organized by tenant/user and document IDs.

### Backend Tests and Diagnostics

- [backend/test_auth2.py](backend/test_auth2.py) - Authentication-related test or experiment script.
- [backend/test_db.py](backend/test_db.py) - Database connectivity or schema test script.
- [backend/test_dns.py](backend/test_dns.py) - DNS/network check script.
- [backend/test_dns2.py](backend/test_dns2.py) - Additional DNS/network check script.
- [backend/test_embed.py](backend/test_embed.py) - Embedding pipeline test script.
- [backend/test_integrations.py](backend/test_integrations.py) - Integration validation script.
- [backend/test_ready.py](backend/test_ready.py) - Readiness probe test script.

### Backend Environment and Packaging

- [backend/requirements.txt](backend/requirements.txt) - Python dependency list for the backend.
- [backend/pyproject.toml](backend/pyproject.toml) - Modern Python project metadata and dependency configuration.
- [backend/.env](backend/.env) - Local environment settings and secrets for backend development.
- [backend/.dockerignore](backend/.dockerignore) - Files excluded from backend Docker build context.
- [backend/.python-version](backend/.python-version) - Python version pin for local tooling.

### Backend Runtime Artifacts

- [backend/__pycache__/](backend/) - Compiled Python bytecode generated by the interpreter.
- [backend/data/blobs/](backend/data/blobs/) - Runtime document storage produced by ingestion and uploads.
- [backend/data/bm25_index/](backend/data/bm25_index/) - Runtime sparse search index artifacts.
- [backend/db/models/__pycache__/](backend/db/models/) - Compiled model bytecode.
- [backend/pipeline/__pycache__/](backend/pipeline/) - Compiled pipeline bytecode.
- [backend/retrieval/__pycache__/](backend/retrieval/) - Compiled retrieval bytecode.
- [backend/routes/__pycache__/](backend/routes/) - Compiled route bytecode.
- [backend/security/__pycache__/](backend/security/) - Compiled security bytecode.
- [backend/services/__pycache__/](backend/services/) - Compiled service bytecode.
- [backend/tasks/__pycache__/](backend/tasks/) - Compiled task bytecode.

## Frontend

### Frontend Root Configuration

- [frontend/package.json](frontend/package.json) - Frontend package metadata, scripts, and dependency manifest.
- [frontend/package-lock.json](frontend/package-lock.json) - Locked dependency graph for reproducible installs.
- [frontend/next.config.ts](frontend/next.config.ts) - Next.js configuration.
- [frontend/tsconfig.json](frontend/tsconfig.json) - TypeScript compiler options.
- [frontend/tailwind.config.ts](frontend/tailwind.config.ts) - Tailwind content scanning and theme extension configuration.
- [frontend/postcss.config.mjs](frontend/postcss.config.mjs) - PostCSS configuration for Tailwind processing.
- [frontend/eslint.config.mjs](frontend/eslint.config.mjs) - ESLint rule configuration.
- [frontend/components.json](frontend/components.json) - shadcn/ui component registry configuration.
- [frontend/README.md](frontend/README.md) - Frontend setup and architecture guide.
- [frontend/CLAUDE.md](frontend/CLAUDE.md) - Frontend-specific agent/instruction context.
- [frontend/frontend_summary_raw.txt](frontend/frontend_summary_raw.txt) - Raw frontend summary and file index reference.
- [frontend/.gitignore](frontend/.gitignore) - Frontend ignore rules.
- [frontend/.env.local](frontend/.env.local) - Local frontend environment configuration.
- [frontend/.env.local.example](frontend/.env.local.example) - Example local environment file.
- [frontend/next-env.d.ts](frontend/next-env.d.ts) - Next.js TypeScript type declarations.

### Frontend App Shell

- [frontend/app/layout.tsx](frontend/app/layout.tsx) - Root application layout and metadata.
- [frontend/app/globals.css](frontend/app/globals.css) - Global styles, theme variables, and Tailwind layers.
- [frontend/app/favicon.ico](frontend/app/favicon.ico) - App favicon.

### Frontend Route Groups: Marketing

- [frontend/app/(marketing)/layout.tsx](frontend/app/%28marketing%29/layout.tsx) - Marketing site layout.
- [frontend/app/(marketing)/page.tsx](frontend/app/%28marketing%29/page.tsx) - Marketing landing/home page.

#### Marketing Components

- [frontend/components/marketing/Navbar.tsx](frontend/components/marketing/Navbar.tsx) - Top navigation for marketing pages.
- [frontend/components/marketing/HeroSection.tsx](frontend/components/marketing/HeroSection.tsx) - Main hero content block.
- [frontend/components/marketing/FeaturesSection.tsx](frontend/components/marketing/FeaturesSection.tsx) - Feature showcase section.
- [frontend/components/marketing/DeveloperSection.tsx](frontend/components/marketing/DeveloperSection.tsx) - Developer-oriented value proposition section.
- [frontend/components/marketing/ComparisonSection.tsx](frontend/components/marketing/ComparisonSection.tsx) - Product comparison section.
- [frontend/components/marketing/TrustedTechSection.tsx](frontend/components/marketing/TrustedTechSection.tsx) - Technology trust/stack section.
- [frontend/components/marketing/TestimonialsSection.tsx](frontend/components/marketing/TestimonialsSection.tsx) - Social proof/testimonials section.
- [frontend/components/marketing/TimelineSection.tsx](frontend/components/marketing/TimelineSection.tsx) - Timeline or roadmap section.
- [frontend/components/marketing/CtaSection.tsx](frontend/components/marketing/CtaSection.tsx) - Final conversion call-to-action section.
- [frontend/components/marketing/Footer.tsx](frontend/components/marketing/Footer.tsx) - Marketing page footer.

### Frontend Route Groups: Auth

- [frontend/app/(auth)/layout.tsx](frontend/app/%28auth%29/layout.tsx) - Authentication layout shell.
- [frontend/app/(auth)/login/page.tsx](frontend/app/%28auth%29/login/page.tsx) - Login page.
- [frontend/app/(auth)/signup/page.tsx](frontend/app/%28auth%29/signup/page.tsx) - Signup page.
- [frontend/app/(auth)/signup/check-email/page.tsx](frontend/app/%28auth%29/signup/check-email/page.tsx) - Email confirmation follow-up page.
- [frontend/app/(auth)/verify-email/page.tsx](frontend/app/%28auth%29/verify-email/page.tsx) - Email verification page.
- [frontend/app/(auth)/forgot-password/page.tsx](frontend/app/%28auth%29/forgot-password/page.tsx) - Password reset request page.
- [frontend/app/(auth)/reset-password/page.tsx](frontend/app/%28auth%29/reset-password/page.tsx) - Password reset submission page.
- [frontend/app/(auth)/accept-invite/page.tsx](frontend/app/%28auth%29/accept-invite/page.tsx) - Invite acceptance page.
- [frontend/app/(auth)/oauth/callback/page.tsx](frontend/app/%28auth%29/oauth/callback/page.tsx) - OAuth callback handler page.

#### Auth Components

- [frontend/components/auth/RequireAuth.tsx](frontend/components/auth/RequireAuth.tsx) - Route guard that redirects unauthenticated users.
- [frontend/components/auth/VerifyEmailNotice.tsx](frontend/components/auth/VerifyEmailNotice.tsx) - Verification reminder UI.
- [frontend/components/auth/ResetPasswordForm.tsx](frontend/components/auth/ResetPasswordForm.tsx) - Password reset form.
- [frontend/components/auth/ForgotPasswordForm.tsx](frontend/components/auth/ForgotPasswordForm.tsx) - Password reset request form.

### Frontend Route Groups: Dashboard

- [frontend/app/(dashboard)/layout.tsx](frontend/app/%28dashboard%29/layout.tsx) - Dashboard layout that wraps authenticated sections with `AppLayout`.
- [frontend/app/(dashboard)/chat/page.tsx](frontend/app/%28dashboard%29/chat/page.tsx) - Main chat experience for conversational RAG.
- [frontend/app/(dashboard)/search/page.tsx](frontend/app/%28dashboard%29/search/page.tsx) - Search debug and retrieval inspection page.
- [frontend/app/(dashboard)/documents/page.tsx](frontend/app/%28dashboard%29/documents/page.tsx) - Documents catalog and management page.
- [frontend/app/(dashboard)/ingestion/page.tsx](frontend/app/%28dashboard%29/ingestion/page.tsx) - Ingestion job monitoring and upload page.
- [frontend/app/(dashboard)/analytics/page.tsx](frontend/app/%28dashboard%29/analytics/page.tsx) - Analytics and metrics dashboard page.
- [frontend/app/(dashboard)/tools/page.tsx](frontend/app/%28dashboard%29/tools/page.tsx) - Tool catalog and management page.
- [frontend/app/(dashboard)/settings/page.tsx](frontend/app/%28dashboard%29/settings/page.tsx) - User/system settings page.

#### Dashboard Layout Components

- [frontend/components/layout/AppLayout.tsx](frontend/components/layout/AppLayout.tsx) - Main application chrome, sidebar, conversation state, and layout coordination.
- [frontend/components/layout/Sidebar.tsx](frontend/components/layout/Sidebar.tsx) - Primary navigation sidebar.
- [frontend/components/layout/TopBar.tsx](frontend/components/layout/TopBar.tsx) - Page header/top bar.
- [frontend/components/layout/StatusBar.tsx](frontend/components/layout/StatusBar.tsx) - Status and health strip.
- [frontend/components/layout/ConversationList.tsx](frontend/components/layout/ConversationList.tsx) - Conversation navigator/list component.
- [frontend/components/layout/PlaceholderPage.tsx](frontend/components/layout/PlaceholderPage.tsx) - Fallback/placeholder shell for unavailable sections.

#### Dashboard Chat Components

- [frontend/components/chat/ChatWindow.tsx](frontend/components/chat/ChatWindow.tsx) - Main chat viewport and interaction surface.
- [frontend/components/chat/ChatInput.tsx](frontend/components/chat/ChatInput.tsx) - Message input composer.
- [frontend/components/chat/MessageBubble.tsx](frontend/components/chat/MessageBubble.tsx) - Individual chat message rendering.
- [frontend/components/chat/MessageActions.tsx](frontend/components/chat/MessageActions.tsx) - Message-level actions such as copy or regenerate.
- [frontend/components/chat/CitationList.tsx](frontend/components/chat/CitationList.tsx) - Citation list for answer grounding.
- [frontend/components/chat/SuggestedFollowUps.tsx](frontend/components/chat/SuggestedFollowUps.tsx) - Suggested next-question chips.
- [frontend/components/chat/StreamingIndicator.tsx](frontend/components/chat/StreamingIndicator.tsx) - Streaming state indicator.
- [frontend/components/chat/PipelineVisualization.tsx](frontend/components/chat/PipelineVisualization.tsx) - Visual explanation of pipeline stages.

#### Dashboard Search Components

- [frontend/components/search/SearchInputArea.tsx](frontend/components/search/SearchInputArea.tsx) - Search query entry and controls.
- [frontend/components/search/SearchForm.tsx](frontend/components/search/SearchForm.tsx) - Search form wrapper.
- [frontend/components/search/SearchFiltersPanel.tsx](frontend/components/search/SearchFiltersPanel.tsx) - Advanced retrieval filters panel.
- [frontend/components/search/SearchAnalyticsPanel.tsx](frontend/components/search/SearchAnalyticsPanel.tsx) - Search analytics side panel.
- [frontend/components/search/ResultCard.tsx](frontend/components/search/ResultCard.tsx) - Base result rendering card.
- [frontend/components/search/AdvancedResultCard.tsx](frontend/components/search/AdvancedResultCard.tsx) - Detailed result card used for richer retrieval output.
- [frontend/components/search/FilterBuilder.tsx](frontend/components/search/FilterBuilder.tsx) - Filter construction UI.

#### Dashboard Document Components

- [frontend/components/documents/DocumentStatsRow.tsx](frontend/components/documents/DocumentStatsRow.tsx) - Document summary statistics row.
- [frontend/components/documents/DocumentListArea.tsx](frontend/components/documents/DocumentListArea.tsx) - Document list/table area.
- [frontend/components/documents/DocumentDetailPanel.tsx](frontend/components/documents/DocumentDetailPanel.tsx) - Selected document details panel.

#### Dashboard Ingestion Components

- [frontend/components/ingestion/IngestionStatsRow.tsx](frontend/components/ingestion/IngestionStatsRow.tsx) - Ingestion summary statistics row.
- [frontend/components/ingestion/IngestionUploadArea.tsx](frontend/components/ingestion/IngestionUploadArea.tsx) - File upload and ingest trigger area.
- [frontend/components/ingestion/IngestionConfigArea.tsx](frontend/components/ingestion/IngestionConfigArea.tsx) - Ingestion configuration controls.
- [frontend/components/ingestion/IngestionListArea.tsx](frontend/components/ingestion/IngestionListArea.tsx) - Ingestion job list area.
- [frontend/components/ingestion/IngestionDetailPanel.tsx](frontend/components/ingestion/IngestionDetailPanel.tsx) - Ingestion job detail panel.

#### Dashboard Analytics Components

- [frontend/components/analytics/AnalyticsStatsRow.tsx](frontend/components/analytics/AnalyticsStatsRow.tsx) - High-level analytics metrics row.
- [frontend/components/analytics/AnalyticsChartsGrid.tsx](frontend/components/analytics/AnalyticsChartsGrid.tsx) - Multi-chart analytics grid.
- [frontend/components/analytics/AnalyticsMetricsRow.tsx](frontend/components/analytics/AnalyticsMetricsRow.tsx) - Retrieval-quality metrics row.
- [frontend/components/analytics/AnalyticsRightPanel.tsx](frontend/components/analytics/AnalyticsRightPanel.tsx) - Side panel with top queries or related analytics.

#### Dashboard Tools Components

- [frontend/components/tools/ToolsStatsRow.tsx](frontend/components/tools/ToolsStatsRow.tsx) - Tool usage statistics row.
- [frontend/components/tools/ToolListArea.tsx](frontend/components/tools/ToolListArea.tsx) - Tool list and management area.
- [frontend/components/tools/ToolsRightPanel.tsx](frontend/components/tools/ToolsRightPanel.tsx) - Tool details or activity side panel.

#### Dashboard Settings Components

- [frontend/components/settings/SettingsTabs.tsx](frontend/components/settings/SettingsTabs.tsx) - Settings tab navigation.
- [frontend/components/settings/SettingsGrid.tsx](frontend/components/settings/SettingsGrid.tsx) - Grid layout for settings panels.
- [frontend/components/settings/SettingsRightPanel.tsx](frontend/components/settings/SettingsRightPanel.tsx) - Settings side panel.
- [frontend/components/settings/DangerZone.tsx](frontend/components/settings/DangerZone.tsx) - Destructive action area for dangerous operations.

#### Dashboard Context Components

- [frontend/components/context/RetrievalDetailsPanel.tsx](frontend/components/context/RetrievalDetailsPanel.tsx) - Retrieval details side panel used in chat.
- [frontend/components/context/ConversationContextPanel.tsx](frontend/components/context/ConversationContextPanel.tsx) - Conversation context helper panel.

#### Other Shared Frontend Components

- [frontend/components/sources/SourcesPanel.tsx](frontend/components/sources/SourcesPanel.tsx) - Source list/details panel for retrieved citations.
- [frontend/components/dashboard/MetricsPanel.tsx](frontend/components/dashboard/MetricsPanel.tsx) - Generic dashboard metrics display.
- [frontend/components/dashboard/HealthStatusCard.tsx](frontend/components/dashboard/HealthStatusCard.tsx) - Health status card for component readiness.
- [frontend/components/dashboard/ComponentHealthGrid.tsx](frontend/components/dashboard/ComponentHealthGrid.tsx) - Grid of service health indicators.
- [frontend/components/ui/button.tsx](frontend/components/ui/button.tsx) - Shared button primitive.
- [frontend/components/ui/input.tsx](frontend/components/ui/input.tsx) - Shared input primitive.
- [frontend/components/ui/textarea.tsx](frontend/components/ui/textarea.tsx) - Shared textarea primitive.
- [frontend/components/ui/card.tsx](frontend/components/ui/card.tsx) - Shared card primitive.
- [frontend/components/ui/badge.tsx](frontend/components/ui/badge.tsx) - Shared badge primitive.
- [frontend/components/ui/spinner.tsx](frontend/components/ui/spinner.tsx) - Loading spinner primitive.

### Frontend Libraries and Hooks

- [frontend/lib/utils.ts](frontend/lib/utils.ts) - Shared utility helpers, typically class-name composition and formatting helpers.
- [frontend/lib/types/models.ts](frontend/lib/types/models.ts) - Frontend TypeScript models mirroring backend contracts.
- [frontend/lib/types/backend.ts](frontend/lib/types/backend.ts) - Backend-specific frontend type helpers or compatibility types.
- [frontend/lib/auth/session.ts](frontend/lib/auth/session.ts) - JWT token storage, role decoding, and user-info extraction from the browser.
- [frontend/lib/hooks/useChat.ts](frontend/lib/hooks/useChat.ts) - Streaming chat state machine and request orchestration.
- [frontend/lib/hooks/useSearch.ts](frontend/lib/hooks/useSearch.ts) - Search request state and result management.
- [frontend/lib/hooks/useHealthPolling.ts](frontend/lib/hooks/useHealthPolling.ts) - Polling hook for service health.
- [frontend/lib/hooks/useConversations.ts](frontend/lib/hooks/useConversations.ts) - Conversation list/state hook.

#### Frontend API Clients

- [frontend/lib/api/client.ts](frontend/lib/api/client.ts) - Shared HTTP client with base URL handling, JWT injection, and unified error handling.
- [frontend/lib/api/auth.ts](frontend/lib/api/auth.ts) - Auth API wrapper.
- [frontend/lib/api/query.ts](frontend/lib/api/query.ts) - Query and stream-query API wrapper.
- [frontend/lib/api/search.ts](frontend/lib/api/search.ts) - Search API wrapper.
- [frontend/lib/api/ingest.ts](frontend/lib/api/ingest.ts) - Ingestion API wrapper.
- [frontend/lib/api/documents.ts](frontend/lib/api/documents.ts) - Documents API wrapper.
- [frontend/lib/api/conversations.ts](frontend/lib/api/conversations.ts) - Conversations API wrapper.
- [frontend/lib/api/analytics.ts](frontend/lib/api/analytics.ts) - Analytics API wrapper.
- [frontend/lib/api/settings.ts](frontend/lib/api/settings.ts) - Settings and admin API wrapper.
- [frontend/lib/api/tools.ts](frontend/lib/api/tools.ts) - Tools API wrapper.
- [frontend/lib/api/notifications.ts](frontend/lib/api/notifications.ts) - Notifications API wrapper.
- [frontend/lib/api/health.ts](frontend/lib/api/health.ts) - Health-check API wrapper.

#### Frontend Storage

- [frontend/lib/storage/conversationStore.ts](frontend/lib/storage/conversationStore.ts) - Local conversation persistence, likely for client-side caching or offline state.
- [frontend/lib/utils/sse.ts](frontend/lib/utils/sse.ts) - Server-sent events parser used by streaming chat.

### Frontend Public Assets

- [frontend/public/logo.png](frontend/public/logo.png) - Brand logo used in the UI.
- [frontend/public/file.svg](frontend/public/file.svg) - File icon asset.
- [frontend/public/globe.svg](frontend/public/globe.svg) - Globe icon asset.
- [frontend/public/next.svg](frontend/public/next.svg) - Next.js logo asset.
- [frontend/public/vercel.svg](frontend/public/vercel.svg) - Vercel logo asset.
- [frontend/public/window.svg](frontend/public/window.svg) - Window UI asset.

### Frontend Runtime and Build Artifacts

- [frontend/node_modules/](frontend/) - Installed frontend dependencies.
- [frontend/.next/](frontend/) - Next.js build and runtime output.

## Runtime Services and Data Stores

- [qdrant/](qdrant/) - Vector database runtime directory, including storage and snapshots used by Qdrant.
- [qdrant/snapshots/](qdrant/snapshots/) - Qdrant snapshot exports.
- [qdrant/storage/](qdrant/storage/) - Qdrant persistent vector data.
- [redis/](redis/) - Redis distribution folder used to run the local Redis server on Windows.
- [redis/redis-server.exe](redis/redis-server.exe) - Redis server executable.
- [redis/redis-cli.exe](redis/redis-cli.exe) - Redis command-line client.
- [redis/redis.windows.conf](redis/redis.windows.conf) - Redis configuration for local development.
- [redis/redis.windows-service.conf](redis/redis.windows-service.conf) - Redis Windows service configuration.
- [storage/](storage/) - Shared storage folder containing Raft state, aliases, and collections for the local embedded stateful services.

## Notes on Generated Files and Directories

- Files under `__pycache__` are Python bytecode artifacts and do not contain application logic.
- Files under `backend/data/blobs/` are user/document payloads produced by ingestion or upload flows.
- Files under `backend/data/bm25_index/` and `storage/` are runtime indexes or service state, not hand-authored source.
- The repo contains several `.pyc` files and snapshot/runtime artifacts; they are included here only so their purpose is clear, but they should be treated as generated output.

## Workflow Summary

- Frontend auth pages handle login, signup, email verification, password reset, and invite acceptance.
- Authenticated users enter the dashboard shell and can chat, search, inspect documents, upload ingestion jobs, view analytics, manage tools, and change settings.
- Chat requests flow through the FastAPI `/api/query` and `/api/stream` endpoints, which use the RAG pipeline to retrieve, rerank, ground, and generate answers.
- Search requests flow through `/api/search`, `/api/search/web`, and `/api/search/code` for retrieval debug and external lookup.
- Ingestion scans documents, extracts text, chunks, embeds, indexes into Qdrant/BM25, and persists metadata plus blobs for later retrieval.
- Telemetry, conversation history, job logs, notifications, and settings are persisted in Postgres-backed tables so the app can keep state across sessions.
