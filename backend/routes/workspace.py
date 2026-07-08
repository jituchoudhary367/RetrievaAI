"""
routes/workspace.py

Enterprise AI Control Center API — workspace-scoped provider management.

All endpoints are scoped to the authenticated user (user = workspace owner).
Does NOT touch any existing routes/settings.py endpoints.

Mounted at: /api/workspace
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from db.models.user import User
from security.auth import get_current_user
from services.workspace.provider_service import get_provider_service
from services.workspace.runtime_config_service import get_runtime_config_service
from services.workspace.model_discovery import get_model_discovery
from services.workspace.connection_tester import (
    test_llm_connection,
    test_embedding_connection,
    test_search_connection,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/workspace", tags=["workspace"])


# ── Pydantic schemas ───────────────────────────────────────────────────────────

class ProviderCreate(BaseModel):
    provider_type: str = Field(..., description="llm | embedding | search")
    provider_name: str = Field(..., description="groq | openai | anthropic | etc.")
    display_name: Optional[str] = None
    config: Dict[str, Any] = Field(default_factory=dict)


class ProviderUpdate(BaseModel):
    display_name: Optional[str] = None
    config: Dict[str, Any] = Field(default_factory=dict)


class RuntimeConfigUpdate(BaseModel):
    updates: Dict[str, Any]


class SingleRuntimeUpdate(BaseModel):
    value: Any


# ── Provider endpoints ─────────────────────────────────────────────────────────

@router.get("/providers")
async def list_providers(
    provider_type: Optional[str] = Query(None, description="Filter: llm | embedding | search"),
    current_user: User = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    """List all workspace providers, optionally filtered by type."""
    svc = get_provider_service()
    providers = await svc.list_providers(current_user.id, provider_type=provider_type)
    # Remove internal _decrypted_config from API response
    for p in providers:
        p.pop("_decrypted_config", None)
    return providers


@router.get("/providers/{provider_id}")
async def get_provider(
    provider_id: str,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    svc = get_provider_service()
    provider = await svc.get_provider(current_user.id, provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    provider.pop("_decrypted_config", None)
    return provider


@router.post("/providers", status_code=201)
async def create_provider(
    body: ProviderCreate,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Add a new provider to the workspace."""
    svc = get_provider_service()
    try:
        provider = await svc.create_provider(
            user_id=current_user.id,
            provider_type=body.provider_type,
            provider_name=body.provider_name,
            config=body.config,
            display_name=body.display_name,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    provider.pop("_decrypted_config", None)
    return provider


@router.put("/providers/{provider_id}")
async def update_provider(
    provider_id: str,
    body: ProviderUpdate,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Update provider config (partial update — merges with existing)."""
    svc = get_provider_service()
    provider = await svc.update_provider(
        user_id=current_user.id,
        provider_id=provider_id,
        config=body.config,
        display_name=body.display_name,
    )
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    provider.pop("_decrypted_config", None)
    return provider


@router.delete("/providers/{provider_id}", status_code=204)
async def delete_provider(
    provider_id: str,
    current_user: User = Depends(get_current_user),
):
    """Remove a provider from the workspace."""
    svc = get_provider_service()
    deleted = await svc.delete_provider(current_user.id, provider_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Provider not found")


@router.post("/providers/{provider_id}/test")
async def test_provider(
    provider_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Test provider connection and update its status."""
    svc = get_provider_service()
    provider = await svc.get_provider(current_user.id, provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    # Mark as validating
    await svc.update_status(provider_id, "validating")

    decrypted = svc.get_decrypted_config(provider)
    provider_type = provider["provider_type"]
    provider_name = provider["provider_name"]

    if provider_type == "llm":
        result = await test_llm_connection(provider_name, decrypted)
    elif provider_type == "embedding":
        result = await test_embedding_connection(provider_name, decrypted)
    elif provider_type == "search":
        result = await test_search_connection(provider_name, decrypted)
    else:
        result = {"success": False, "error": f"Unknown provider type: {provider_type}"}

    new_status = "connected" if result["success"] else "error"
    health = "healthy" if result["success"] else "down"
    await svc.update_status(
        provider_id,
        status=new_status,
        health_status=health,
        latency_ms=result.get("latency_ms"),
        error=result.get("error"),
    )
    return {**result, "status": new_status, "provider_id": provider_id}


@router.post("/providers/{provider_id}/set-default")
async def set_default_provider(
    provider_id: str,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Set provider as the default for its type."""
    svc = get_provider_service()
    provider = await svc.get_provider(current_user.id, provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    success = await svc.set_default(current_user.id, provider_id, provider["provider_type"])
    return {"success": success}


@router.post("/providers/{provider_id}/set-fallback")
async def set_fallback_provider(
    provider_id: str,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Set provider as the fallback for its type."""
    svc = get_provider_service()
    provider = await svc.get_provider(current_user.id, provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    success = await svc.set_fallback(current_user.id, provider_id, provider["provider_type"])
    return {"success": success}


# ── Model endpoints ─────────────────────────────────────────────────────────────

@router.get("/models")
async def list_models(
    provider_name: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    """List cached models from the model catalog."""
    from sqlalchemy import select
    from db.engine import async_session_factory
    from db.models.workspace_settings import WorkspaceModel
    async with async_session_factory() as db:
        q = select(WorkspaceModel).where(WorkspaceModel.user_id == current_user.id)
        if provider_name:
            q = q.where(WorkspaceModel.provider_name == provider_name)
        result = await db.execute(q.order_by(WorkspaceModel.provider_name, WorkspaceModel.model_name))
        rows = result.scalars().all()
    disc = get_model_discovery()
    return [disc._row_to_dict(r) for r in rows]


@router.post("/models/discover/{provider_id}")
async def discover_models(
    provider_id: str,
    current_user: User = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    """Fetch models from a provider's API and refresh the cache."""
    svc = get_provider_service()
    provider = await svc.get_provider(current_user.id, provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    decrypted = svc.get_decrypted_config(provider)
    disc = get_model_discovery()
    # Force refresh by clearing cached entry first
    from sqlalchemy import delete as sa_delete
    from db.engine import async_session_factory
    from db.models.workspace_settings import WorkspaceModel
    async with async_session_factory() as db:
        await db.execute(
            sa_delete(WorkspaceModel).where(
                WorkspaceModel.user_id == current_user.id,
                WorkspaceModel.provider_name == provider["provider_name"],
            )
        )
        await db.commit()
    models = await disc.get_models(
        user_id=current_user.id,
        provider_name=provider["provider_name"],
        api_key=decrypted.get("api_key", ""),
        endpoint=decrypted.get("endpoint", ""),
    )
    return models


@router.post("/models/{model_id}/favorite")
async def toggle_model_favorite(
    model_id: str,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    disc = get_model_discovery()
    success = await disc.toggle_favorite(current_user.id, model_id)
    return {"success": success}


@router.post("/models/{model_id}/set-default")
async def set_default_model(
    model_id: str,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    from sqlalchemy import select
    from db.engine import async_session_factory
    from db.models.workspace_settings import WorkspaceModel
    async with async_session_factory() as db:
        result = await db.execute(
            select(WorkspaceModel).where(
                WorkspaceModel.id == model_id,
                WorkspaceModel.user_id == current_user.id,
            )
        )
        row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Model not found")
    disc = get_model_discovery()
    success = await disc.set_default_model(current_user.id, model_id, row.provider_name)
    return {"success": success}


# ── Runtime Config endpoints ────────────────────────────────────────────────────

@router.get("/runtime")
async def get_runtime_config(
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get all runtime configuration (workspace overrides merged with system defaults)."""
    svc = get_runtime_config_service()
    return await svc.get_all(current_user.id)


@router.put("/runtime")
async def update_runtime_config(
    body: RuntimeConfigUpdate,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Bulk update runtime config. Changes take effect immediately (no restart needed)."""
    svc = get_runtime_config_service()
    await svc.bulk_update(current_user.id, body.updates)
    return await svc.get_all(current_user.id)


@router.put("/runtime/{key}")
async def update_single_runtime_key(
    key: str,
    body: SingleRuntimeUpdate,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Update a single runtime config key."""
    svc = get_runtime_config_service()
    await svc.set(current_user.id, key, body.value)
    return {"key": key, "value": body.value, "success": True}


# ── Health & Usage ──────────────────────────────────────────────────────────────

@router.get("/health")
async def get_workspace_health(
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """System health status for all services."""
    from services.health_sampler import HealthSampler
    sampler = HealthSampler()
    health = await sampler.sample()
    return health


@router.get("/usage")
async def get_workspace_usage(
    days: int = Query(7, ge=1, le=90),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """AI usage statistics for the workspace."""
    from sqlalchemy import select, func as sqlfunc
    from db.engine import async_session_factory
    from db.models.telemetry import QueryEvent
    from datetime import datetime, timezone, timedelta

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    async with async_session_factory() as db:
        result = await db.execute(
            select(
                sqlfunc.count(QueryEvent.id).label("total_queries"),
                sqlfunc.sum(QueryEvent.total_tokens).label("total_tokens"),
                sqlfunc.avg(QueryEvent.total_latency_ms).label("avg_latency_ms"),
                sqlfunc.sum(
                    sqlfunc.cast(QueryEvent.used_cache, sqlfunc.Integer if hasattr(sqlfunc, "Integer") else QueryEvent.used_cache)
                ).label("cache_hits"),
            ).where(
                QueryEvent.user_id == current_user.id,
                QueryEvent.created_at >= cutoff,
            )
        )
        row = result.one()

    total = int(row.total_queries or 0)
    cache_hits = int(row.cache_hits or 0)
    return {
        "days": days,
        "total_queries": total,
        "total_tokens": int(row.total_tokens or 0),
        "avg_latency_ms": round(float(row.avg_latency_ms or 0), 1),
        "cache_hit_rate": round(cache_hits / total * 100, 1) if total > 0 else 0,
        "cache_hits": cache_hits,
    }


__all__ = ["router"]
