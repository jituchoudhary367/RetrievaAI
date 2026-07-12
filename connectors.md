# RetrievaAI — Universal Enterprise Connector Framework
# Full Phase Plan (Antigravity Format, Phases 21–40)

> Base path used below: `c:/Users/Jitendra Chaudhary/OneDrive/Desktop/RAG_application/`
> Feed one phase into Antigravity at a time, in order. Do not start Phase N+1 until Phase N's Verification Plan has actually passed.

---

# Phase 21: Universal Connector Framework Skeleton

## Goal Description
Establish the foundational abstract interfaces, capability enumerations, payload structures, and exception classes for the new modular connector framework. This guarantees that all future enterprise connectors — and eventually the refactored Google Drive connector — adhere to a unified, scalable contract.

## Proposed Changes

### Base Framework Contracts

#### [NEW] [backend/connectors/base/\_\_init\_\_.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/connectors/base/__init__.py)
- Marks the directory as a Python package.

#### [NEW] [backend/connectors/base/metadata.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/connectors/base/metadata.py)
- Defines `ConnectorFileMetadata` and `ConnectorPermission` data models.

#### [NEW] [backend/connectors/base/sync.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/connectors/base/sync.py)
- Defines `SyncMode` enum, `SyncResult`, and `SyncCursor` structures.

#### [NEW] [backend/connectors/base/capabilities.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/connectors/base/capabilities.py)
- Defines the `Capability` enum (`OAUTH`, `INCREMENTAL_SYNC`, `WEBHOOKS`, `DELTA_API`, etc.) and `CapabilitySet`.

#### [NEW] [backend/connectors/base/connector.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/connectors/base/connector.py)
- Defines the `BaseConnector` Abstract Base Class (ABC) providing the strict contract for `authenticate`, `refresh_token`, `full_sync`, `incremental_sync`, `download_file`, `detect_deletes`, `get_permissions`, `health_check`, `register_webhook`.

#### [NEW] [backend/connectors/base/payload.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/connectors/base/payload.py)
- Defines `IngestionTaskPayload` — the strict boundary contract ("the seam") that bridges the connector world into the existing ingestion orchestrator/Celery tasks.

#### [NEW] [backend/connectors/base/exceptions.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/connectors/base/exceptions.py)
- Defines shared exception classes: `ConnectorAuthError`, `ConnectorRateLimitError`, `ConnectorSyncError`, `ConnectorWebhookError`.

#### [NEW] [backend/connectors/base/auth.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/connectors/base/auth.py)
- Defines `BaseAuthProvider` with `OAuth2AuthProvider`, `APIKeyAuthProvider`, `ServiceAccountAuthProvider` subclasses (interfaces only — no live credentials logic yet).

#### [NEW] [backend/connectors/base/webhook.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/connectors/base/webhook.py)
- Defines `BaseWebhookHandler` interface for connectors that support push-based updates.

## Verification Plan

### Automated Tests
- I will create a test stub `backend/tests/test_connector_payload.py` to confirm that `IngestionTaskPayload` can be safely constructed and conforms to the shape expected by the downstream ingestion components.
- I will create `backend/tests/test_base_connector_contract.py` asserting `BaseConnector` cannot be instantiated directly and that a minimal dummy subclass implementing all abstract methods can be.

### Manual Verification
- Verify that `BaseConnector` correctly inherits `ABC` and compiles cleanly.
- Verify that no existing files outside the new `connectors/base/` directory were touched.
- Run `git diff --stat` and confirm only new files appear.

> [!CAUTION]
> The existing Google Drive implementation and any legacy `backend/connectors/base.py` remain untouched during this phase. They will be refactored to use this new framework in Phase 22, ensuring a zero-break migration.

## Next Steps
Once this Phase 21 plan is approved, implement these files, commit to the `connectors` branch, and proceed to Phase 22.

---

# Phase 22: Refactor Google Drive into the Framework (Reference Implementation)

## Goal Description
Migrate the existing, working Google Drive integration into the new connector framework as its **reference implementation**, without changing observable behavior. Every downstream connector will be built by copying this module's shape.

## Proposed Changes

### Google Drive Adapter

#### [NEW] [backend/connectors/google_drive/\_\_init\_\_.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/connectors/google_drive/__init__.py)
- Package marker.

#### [NEW] [backend/connectors/google_drive/adapter.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/connectors/google_drive/adapter.py)
- `GoogleDriveConnector(BaseConnector)` — ports existing Drive API calls (list, download, delta, permissions) behind the new contract.

#### [NEW] [backend/connectors/google_drive/mapper.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/connectors/google_drive/mapper.py)
- Maps raw Google Drive API objects into `ConnectorFileMetadata` / `ConnectorPermission`.

#### [NEW] [backend/connectors/google_drive/auth.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/connectors/google_drive/auth.py)
- Drive-specific OAuth2 quirks (scopes, refresh handling) implementing `BaseAuthProvider`.

### Legacy Path Retirement (only after new path is verified)

#### [MODIFIED] existing Google Drive route/service file (locate current path, e.g. `backend/services/google_drive_service.py`)
- Re-point calls to `GoogleDriveConnector` adapter methods.
- Old direct-API-call logic deleted **only after** staging parity is confirmed — see Verification Plan.

## Verification Plan

### Automated Tests
- `backend/tests/test_google_drive_adapter.py` — mocked Drive API responses through `full_sync`, `incremental_sync`, `detect_deletes`, `get_permissions`.
- Regression test comparing document counts/checksums indexed via the old path vs. the new adapter path on a fixed fixture set — expect zero diff.

### Manual Verification
- Run a full sync against a real (test) Drive account through the new adapter; confirm indexed document count matches the pre-refactor baseline.
- Run an incremental sync after adding/removing a test file; confirm delta detection is correct.
- Confirm existing Drive-related API responses and frontend behavior are byte-identical to before.

> [!CAUTION]
> Do not delete the legacy Drive code path until the new adapter has passed a full staging regression. Keep both behind a feature flag during transition.

## Next Steps
Approve, implement, verify in staging, remove legacy path, then proceed to Phase 23.

---

# Phase 23: Connector Registry

## Goal Description
Introduce a centralized registry so the rest of the system (orchestrator, scheduler, dashboard) never branches on provider name — only on registered capabilities.

## Proposed Changes

#### [NEW] [backend/connectors/registry.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/connectors/registry.py)
- `ConnectorRegistry` singleton: `register()`, `enable()`, `disable()`, `get(provider_name)`, `list_active()`, `capabilities_of(provider_name)`.
- Dynamic discovery via `importlib` scan of `connectors/*/adapter.py` at startup.

#### [NEW] [backend/connectors/base/registry_entry.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/connectors/base/registry_entry.py)
- `ConnectorRegistryEntry` dataclass: provider name, adapter class, version, capability set, enabled flag.

## Verification Plan

### Automated Tests
- `backend/tests/test_registry.py` — register, disable, re-enable, capability lookup, duplicate-registration rejection.

### Manual Verification
- On app startup, confirm the registry lists exactly one active connector: `google_drive`.
- Confirm disabling `google_drive` via the registry stops new syncs without deleting existing indexed documents.

> [!CAUTION]
> No provider-specific `if provider == "google_drive"` branches are permitted outside `connectors/google_drive/`. Grep the diff for this pattern before approving.

## Next Steps
Proceed to Phase 24 once registry tests pass and startup discovery is confirmed.

---

# Phase 24: Orchestrator + Celery Task Wiring

## Goal Description
Wire the registry to a orchestrator that drives sync and emits one Celery task per discovered file, feeding the existing ingestion pipeline through the `IngestionTaskPayload` seam.

## Proposed Changes

#### [NEW] [backend/connectors/orchestrator.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/connectors/orchestrator.py)
- `ConnectorOrchestrator.run_full_sync(connector_id)` / `run_incremental_sync(connector_id)`.
- Persists discovered files into `connector_files`, builds `IngestionTaskPayload`, dispatches Celery tasks.

#### [NEW] [backend/connectors/tasks.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/connectors/tasks.py)
- Celery tasks: `discover_files_task`, `download_and_enqueue_task`, `sync_connector_task`, `refresh_token_task`.
- `download_and_enqueue_task` calls `adapter.download_file()`, stores bytes to temp/blob storage, builds `IngestionTaskPayload`, and hands off to the **existing, unmodified** ingestion entrypoint.

#### [MODIFIED] [backend/celery_app.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/celery_app.py)
- Register the new task module in the existing Celery app's autodiscover list only — no change to existing task definitions or queue config.

## Verification Plan

### Automated Tests
- `backend/tests/test_orchestrator.py` — mocked adapter emits N files, confirm N Celery tasks dispatched with correctly-shaped payloads.
- Integration test: dispatch one real task end-to-end into the existing ingestion pipeline against a test document, confirm it appears in the catalog exactly as it would via the old Drive path.

### Manual Verification
- Trigger a full sync via the orchestrator for the Drive connector; confirm parallel task execution, retries on induced failure, and correct queue priority behavior (matching existing queue config).

> [!CAUTION]
> `download_and_enqueue_task` must call the existing ingestion entrypoint function **by its existing name and signature** — do not rename or wrap it in a way that changes its public interface.

## Next Steps
Proceed to Phase 25 once end-to-end Celery flow is verified against the existing pipeline.

---

# Phase 25: Connector Manager + REST API + Credential Encryption

## Goal Description
Give operators (and eventually the dashboard) a way to connect/disconnect/pause/resume connectors, and ensure all stored credentials are encrypted at rest using the existing crypto utility.

## Proposed Changes

#### [NEW] [backend/connectors/manager.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/connectors/manager.py)
- `ConnectorManager`: `connect()`, `disconnect()`, `pause()`, `resume()`, `sync_now()`, `rotate_credentials()`.

#### [NEW] [backend/api/routes/connectors.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/api/routes/connectors.py)
- New router: `GET /api/connectors`, `POST /api/connectors`, `POST /api/connectors/{id}/connect`, `/disconnect`, `/pause`, `/resume`, `/sync-now`, `GET /api/connectors/{id}/health`.

#### [MODIFIED] [backend/api/main.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/api/main.py)
- Mount the new router under the existing API app. No changes to existing route registrations.

#### [NEW] [backend/db/models/connector.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/db/models/connector.py)
- SQLAlchemy models: `Connector`, `ConnectorCredential`, `ConnectorSyncState` (additive tables only — see schema in Section 3 of the master plan).

#### [NEW] [backend/db/migrations/xxxx_add_connector_tables.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/db/migrations/xxxx_add_connector_tables.py)
- Alembic migration, additive only.

## Verification Plan

### Automated Tests
- `backend/tests/test_connector_manager.py` and `backend/tests/test_connectors_api.py` — connect/disconnect lifecycle, credential encryption round-trip, no plaintext token ever appears in an API response body.

### Manual Verification
- Confirm `connector_credentials.encrypted_payload` is unreadable without the existing decryption key.
- Confirm existing, unrelated API routes return unchanged responses (spot-check 3–5 pre-existing endpoints).

> [!CAUTION]
> Reuse the existing AES-256-GCM crypto utility already used elsewhere in the platform. Do not introduce a second encryption implementation.

## Next Steps
Proceed to Phase 26 once credential encryption and the connect/disconnect lifecycle are verified.

---

# Phase 26: Connector Scheduler

## Goal Description
Automate periodic sync for connectors without webhook support, with retry-with-backoff and pre-emptive OAuth refresh.

## Proposed Changes

#### [NEW] [backend/connectors/scheduler.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/connectors/scheduler.py)
- Celery-beat schedule builder: reads `connector_sync_state`, enqueues `sync_connector_task` on interval, retries failed syncs with exponential backoff, triggers `refresh_token_task` ahead of expiry.

#### [MODIFIED] [backend/celery_beat_schedule.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/celery_beat_schedule.py)
- Add connector scheduler entries to the existing beat schedule dict — no changes to existing scheduled jobs.

## Verification Plan

### Automated Tests
- `backend/tests/test_scheduler.py` — interval computation, backoff sequence on repeated induced failure, refresh triggered at correct threshold before `oauth_expiry`.

### Manual Verification
- Leave the Drive connector running for one full scheduled interval without manual "Sync Now"; confirm an incremental sync fires automatically.

> [!CAUTION]
> Do not modify any existing Celery-beat entries — only append.

## Next Steps
Proceed to Phase 27 once autonomous scheduling is confirmed in staging.

---

# Phase 27: Health Monitoring + Analytics Wiring

## Goal Description
Populate connector health metrics and surface them through the existing analytics pipeline.

## Proposed Changes

#### [NEW] [backend/connectors/health.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/connectors/health.py)
- `HealthMonitor.check(connector_id)` — writes to `connector_health` (queue depth, OAuth expiry, API quota, webhook status, worker health, avg sync duration, retry count).

#### [MODIFIED] [backend/analytics/ingestion.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/analytics/ingestion.py)
- Register new metric names (`connector.files_synced`, `connector.sync_speed`, `connector.failed_files`, etc.) with the existing analytics ingestion function — no change to the function's existing call sites or metric schema for pre-existing metrics.

## Verification Plan

### Automated Tests
- `backend/tests/test_health_monitor.py` — health snapshot correctness against mocked adapter state.

### Manual Verification
- Confirm existing analytics dashboards (unrelated to connectors) show no regressions.
- Confirm new connector metrics are queryable via the existing analytics API.

> [!CAUTION]
> Only add new metric keys — never rename or repurpose an existing analytics metric name.

## Next Steps
Proceed to Phase 28 once metrics are flowing correctly.

---

# Phase 28: Enterprise Connector Dashboard (Frontend)

## Goal Description
Give operators a UI to manage connectors, built as a fully new route that doesn't disturb existing frontend pages.

## Proposed Changes

#### [NEW] [frontend/app/(dashboard)/connectors/page.tsx](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/frontend/app/(dashboard)/connectors/page.tsx)
- List view: one card per connector — status, last sync, files indexed, failed files, queue status, API usage.

#### [NEW] [frontend/app/(dashboard)/connectors/[connectorId]/page.tsx](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/frontend/app/(dashboard)/connectors/[connectorId]/page.tsx)
- Detail view: connect/disconnect/pause/resume/sync-now/view-logs/reindex/view-files actions.

#### [NEW] [frontend/app/(dashboard)/connectors/components/ConnectorCard.tsx](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/frontend/app/(dashboard)/connectors/components/ConnectorCard.tsx)

#### [MODIFIED] [frontend/app/(dashboard)/layout.tsx](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/frontend/app/(dashboard)/layout.tsx)
- Add a single new nav entry, "Connectors." No other nav items touched.

## Verification Plan

### Automated Tests
- Component tests for `ConnectorCard` and the connect/disconnect action flow (mocked API).

### Manual Verification
- Full click-through: connect Drive, trigger sync now, watch status update, pause, resume, disconnect — all reflected correctly.
- Confirm every pre-existing page in the app renders unchanged.

> [!CAUTION]
> Do not modify shared layout components beyond the single nav-entry addition called out above.

## Next Steps
With Phases 21–28 complete, the framework's walking skeleton is production-ready on Google Drive alone. Proceed to Phase 29 to add the next provider.

---

# Phase 29: OneDrive Connector

## Goal Description
Add OneDrive as the second connector, proving the framework generalizes without touching shared code.

## Proposed Changes

#### [NEW] [backend/connectors/onedrive/\_\_init\_\_.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/connectors/onedrive/__init__.py)

#### [NEW] [backend/connectors/onedrive/adapter.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/connectors/onedrive/adapter.py)
- `OneDriveConnector(BaseConnector)` — OAuth, drive discovery, folder/file listing, download, Delta API incremental sync, change notifications, metadata, permissions.

#### [NEW] [backend/connectors/onedrive/mapper.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/connectors/onedrive/mapper.py)

#### [NEW] [backend/connectors/onedrive/auth.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/connectors/onedrive/auth.py)

## Verification Plan

### Automated Tests
- `backend/tests/test_onedrive_adapter.py` — mocked Graph API responses through full/incremental sync, delete detection, permissions.

### Manual Verification
- Register OneDrive in the registry (feature-flagged off by default), connect a test tenant, run full sync, verify document count; run incremental sync after a file change, verify delta-only ingestion.

> [!CAUTION]
> No changes to `connectors/registry.py`, `orchestrator.py`, `manager.py`, or any Drive/shared file — this phase is additive to `connectors/onedrive/` only, plus a registry entry.

## Next Steps
Proceed to Phase 30 once OneDrive passes staging verification.

---

# Phase 30: SharePoint Connector

## Goal Description
Add SharePoint, traversing Site → Library → Folder → Document, including site-level permission sync.

## Proposed Changes

#### [NEW] [backend/connectors/sharepoint/adapter.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/connectors/sharepoint/adapter.py)
- `SharePointConnector(BaseConnector)`.

#### [NEW] [backend/connectors/sharepoint/mapper.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/connectors/sharepoint/mapper.py)

#### [NEW] [backend/connectors/sharepoint/auth.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/connectors/sharepoint/auth.py)

## Verification Plan

### Automated Tests
- `backend/tests/test_sharepoint_adapter.py` — site/library/folder traversal against mocked Graph API; permission mapping correctness.

### Manual Verification
- Full sync against a test SharePoint site; confirm library and folder structure preserved in `external_path`.

> [!CAUTION]
> May reuse Graph API client patterns from `connectors/onedrive/`, but only via explicit shared helper in `connectors/base/` if truly generic — never a direct import from `connectors/onedrive/` into `connectors/sharepoint/`.

## Next Steps
Proceed to Phase 31.

---

# Phase 31: Confluence Connector

## Goal Description
Add Confluence, converting page bodies to Markdown before they enter the ingestion seam.

## Proposed Changes

#### [NEW] [backend/connectors/confluence/adapter.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/connectors/confluence/adapter.py)
- Spaces → Pages → Attachments → (optional) Comments.

#### [NEW] [backend/connectors/confluence/mapper.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/connectors/confluence/mapper.py)
- Confluence storage-format → Markdown conversion happens here, entirely inside this module.

## Verification Plan

### Automated Tests
- Round-trip test: known storage-format fixture → Markdown → confirm no data loss on tables/links/headings.

### Manual Verification
- Sync a test space; confirm pages retrievable with correct source attribution and readable Markdown formatting.

> [!CAUTION]
> Markdown conversion must happen in `connectors/confluence/mapper.py`, not inside the shared ingestion pipeline.

## Next Steps
Proceed to Phase 32.

---

# Phase 32: Notion Connector

## Goal Description
Add Notion, normalizing its block-tree structure into Markdown.

## Proposed Changes

#### [NEW] [backend/connectors/notion/adapter.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/connectors/notion/adapter.py)
- Workspace → Pages/Databases → Blocks → Attachments.

#### [NEW] [backend/connectors/notion/mapper.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/connectors/notion/mapper.py)
- Recursive block-tree → Markdown normalizer (handles nested toggles, databases, synced blocks).

## Verification Plan

### Automated Tests
- Fixture-based test with a nested database + toggle block page; confirm flattened Markdown preserves hierarchy and content.

### Manual Verification
- Sync a test workspace; spot-check 5 pages of varying structure for fidelity.

> [!CAUTION]
> Deeply nested blocks can recurse expensively — cap recursion depth and log a warning rather than failing the whole sync.

## Next Steps
Proceed to Phase 33.

---

# Phase 33: Slack Connector

## Goal Description
Add Slack, turning channel threads into searchable documents with linked attachments.

## Proposed Changes

#### [NEW] [backend/connectors/slack/adapter.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/connectors/slack/adapter.py)
- Public channels, threads, attachments (PDF/image/doc).

#### [NEW] [backend/connectors/slack/mapper.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/connectors/slack/mapper.py)
- Thread → document mapping; attachments linked via shared `thread_id` in `IngestionTaskPayload.metadata`.

## Verification Plan

### Automated Tests
- Mocked Slack API test confirming thread reconstruction and rate-limit backoff behavior against induced 429 responses.

### Manual Verification
- Sync a test workspace channel; confirm thread documents and their attachments are both retrievable and correctly linked.

> [!CAUTION]
> Respect Slack's tier rate limits explicitly in the adapter — do not rely on the orchestrator's generic retry policy alone.

## Next Steps
Proceed to Phase 34.

---

# Phase 34: GitHub Connector

## Goal Description
Add GitHub, syncing code/Markdown/README/Wiki/Releases, designed for future Issues/PRs/Discussions support.

## Proposed Changes

#### [NEW] [backend/connectors/github/adapter.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/connectors/github/adapter.py)
- Repos → branches → code/Markdown/README/Wiki/Releases.

#### [NEW] [backend/connectors/github/mapper.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/connectors/github/mapper.py)

## Verification Plan

### Automated Tests
- Mocked GitHub API test for large-repo pagination and rate-limit handling.

### Manual Verification
- Sync a test repo; confirm binary/non-code files are excluded or routed per config, and rate limits aren't exceeded.

> [!CAUTION]
> Adding Issues/PRs/Discussions later must be done via new `Capability` flags on this same adapter — do not create a second GitHub connector module.

## Next Steps
Proceed to Phase 35.

---

# Phase 35: Dropbox Connector

## Goal Description
Add Dropbox with webhook-driven incremental sync.

## Proposed Changes

#### [NEW] [backend/connectors/dropbox/adapter.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/connectors/dropbox/adapter.py)
- Implements `register_webhook()` in addition to the standard contract.

#### [NEW] [backend/connectors/dropbox/mapper.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/connectors/dropbox/mapper.py)

#### [NEW] [backend/api/routes/webhooks/dropbox.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/api/routes/webhooks/dropbox.py)
- Inbound webhook receiver, signature-verified, enqueues `sync_connector_task`.

## Verification Plan

### Automated Tests
- Signature verification test (reject unsigned/forged payloads).

### Manual Verification
- Modify a file in a test Dropbox folder; confirm webhook fires and incremental sync ingests only the change, not a full resync.

> [!CAUTION]
> Webhook endpoint must verify Dropbox's signature before touching the queue.

## Next Steps
Proceed to Phase 36.

---

# Phase 36: Object Storage Connectors — S3, Azure Blob, GCS

## Goal Description
Add the three cloud object-storage connectors, each event-driven for incremental sync, each fully isolated.

## Proposed Changes

#### [NEW] [backend/connectors/s3/adapter.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/connectors/s3/adapter.py)
- Buckets/objects, incremental sync via S3 Event Notifications (SQS/SNS).

#### [NEW] [backend/connectors/azure_blob/adapter.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/connectors/azure_blob/adapter.py)
- Containers/blobs, incremental sync via Event Grid.

#### [NEW] [backend/connectors/gcs/adapter.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/connectors/gcs/adapter.py)
- Buckets/objects, incremental sync via Pub/Sub notifications.

## Verification Plan

### Automated Tests
- Per-provider mocked event test confirming an object create/update/delete event maps to the correct `connector_files` state transition.

### Manual Verification
- One end-to-end test per provider against a real test bucket/container.

> [!CAUTION]
> Do not introduce a shared "cloud storage base class" unless the shared logic is truly provider-agnostic and expressed purely via `Capability` flags — resist the urge to abstract prematurely across these three.

## Next Steps
Proceed to Phase 37.

---

# Phase 37: Filesystem Connector

## Goal Description
Add a local-folder watcher for on-premise/self-hosted deployments.

## Proposed Changes

#### [NEW] [backend/connectors/filesystem/adapter.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/connectors/filesystem/adapter.py)
- Uses a file-system watcher (e.g. `watchdog`) for new/modified/deleted file events.

## Verification Plan

### Automated Tests
- Test that a file rename/move does not create a duplicate document (checksum-based identity, not path-based).

### Manual Verification
- Point the connector at a test folder; add, modify, rename, and delete a file; confirm each event produces the correct catalog state.

> [!CAUTION]
> This connector should be clearly flagged in the dashboard as intended for self-hosted/on-prem deployments only.

## Next Steps
Proceed to Phase 38.

---

# Phase 38: Database Connector

## Goal Description
Add scheduled extraction from relational databases, converting rows into searchable documents via a configurable mapping.

## Proposed Changes

#### [NEW] [backend/connectors/database/adapter.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/connectors/database/adapter.py)
- Supports PostgreSQL, MySQL, SQL Server, Oracle via a common driver abstraction.

#### [NEW] [backend/connectors/database/mapper.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/connectors/database/mapper.py)
- Table + column → document template mapping, configurable per connector instance.

## Verification Plan

### Automated Tests
- Test that incremental extraction uses a watermark column (`updated_at`/version) and does not re-read the full table on every sync.

### Manual Verification
- Configure a test table with a mapping; run full then incremental extraction; confirm only changed rows produce new/updated documents.

> [!CAUTION]
> Never store raw DB credentials outside `connector_credentials` (encrypted). Query mapping config itself is not secret and can live in `connectors.config`.

## Next Steps
Proceed to Phase 39.

---

# Phase 39: Generic Webhook Connector

## Goal Description
Allow third-party systems to push arbitrary files directly into the ingestion queue via a signed webhook.

## Proposed Changes

#### [NEW] [backend/connectors/webhook_generic/adapter.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/connectors/webhook_generic/adapter.py)

#### [NEW] [backend/api/routes/webhooks/generic.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/api/routes/webhooks/generic.py)
- Per-connector shared-secret auth, payload size/type validation before enqueue.

## Verification Plan

### Automated Tests
- Reject unsigned, oversized, or malformed requests before they touch the Celery queue.

### Manual Verification
- Send a valid signed test payload; confirm it flows through to ingestion; send an invalid one and confirm rejection with no side effects.

> [!CAUTION]
> This is the connector most exposed to abuse — validate aggressively and rate-limit per shared secret.

## Next Steps
Proceed to Phase 40.

---

# Phase 40: Permission Synchronization Hardening

## Goal Description
Normalize each connected provider's ACL model into a shared internal role enum, stored per document, for future document-level authorization.

## Proposed Changes

#### [NEW] [backend/connectors/permissions.py](file:///c:/Users/Jitendra%20Chaudhary/OneDrive/Desktop/RAG_application/backend/connectors/permissions.py)
- `PermissionSyncService.normalize(provider, raw_permissions) -> list[ConnectorPermission]`.
- Persists to `connector_permissions`.

## Verification Plan

### Automated Tests
- Per-provider mapping test: each provider's native roles (Editor/Viewer/Owner/etc.) map to the correct shared internal role.

### Manual Verification
- Query `connector_permissions` across two different connected providers for the same user; confirm consistent role representation.

> [!CAUTION]
> This phase stores permission metadata only. It does **not** wire ACLs into the actual retrieval-time authorization check — that is a separate, security-reviewed effort, out of scope here.

## Next Steps
With all 20 connectors integrated and permissions normalized, move to a dedicated hardening pass: load testing the orchestrator under many concurrent connectors, and a security review of the credential-encryption and webhook-signature paths before general availability.