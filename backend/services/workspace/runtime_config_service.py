"""
services/workspace/runtime_config_service.py

Workspace-level pipeline tuning stored as a KV table in Postgres.
Falls back to global get_settings() defaults for any key not configured.

Keys and their system defaults:
  chunk_size           → settings.chunking.chunk_size
  chunk_overlap        → settings.chunking.chunk_overlap
  top_k                → settings.retrieval.top_k_final
  rerank_top_n         → settings.retrieval.rerank_top_n
  hybrid_alpha         → settings.retrieval.hybrid_alpha
  cache_ttl            → settings.redis.cache_ttl_seconds
  memory_window        → settings.conversation.max_history_turns
  streaming_enabled    → settings.features.enable_streaming
  crag_enabled         → settings.features.enable_crag
  web_search_enabled   → settings.features.enable_web_search_tool
  code_search_enabled  → settings.features.enable_code_search_tool
  ocr_enabled          → True
  vision_enabled       → False
  telemetry_enabled    → True
  analytics_enabled    → True
  reranking_enabled    → settings.features.enable_reranking
  semantic_cache_enabled → settings.features.enable_semantic_cache
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any, Dict, Optional, Tuple

from sqlalchemy import select
from db.engine import async_session_factory
from db.models.workspace_settings import WorkspaceRuntimeConfig

logger = logging.getLogger(__name__)

_CacheEntry = Tuple[Any, float]
_CACHE_TTL = 60.0  # seconds


def _get_system_defaults() -> Dict[str, Any]:
    """Lazy-load system defaults from global settings."""
    from app.config import get_settings
    cfg = get_settings()
    return {
        "chunk_size": cfg.chunking.chunk_size,
        "chunk_overlap": cfg.chunking.chunk_overlap,
        "top_k": cfg.retrieval.top_k_final,
        "rerank_top_n": cfg.retrieval.rerank_top_n,
        "hybrid_alpha": cfg.retrieval.hybrid_alpha,
        "cache_ttl": cfg.redis.cache_ttl_seconds,
        "memory_window": cfg.conversation.max_history_turns,
        "streaming_enabled": cfg.features.enable_streaming,
        "crag_enabled": cfg.features.enable_crag,
        "web_search_enabled": cfg.features.enable_web_search_tool,
        "code_search_enabled": cfg.features.enable_code_search_tool,
        "reranking_enabled": cfg.features.enable_reranking,
        "semantic_cache_enabled": cfg.features.enable_semantic_cache,
        "ocr_enabled": True,
        "vision_enabled": False,
        "telemetry_enabled": True,
        "analytics_enabled": True,
        "embedding_batch_size": cfg.embedding.batch_size,
        "bm25_weight": 1.0 - cfg.retrieval.hybrid_alpha,
        "vector_weight": cfg.retrieval.hybrid_alpha,
    }


class WorkspaceRuntimeConfigService:
    """
    Reads/writes workspace runtime config with an in-process TTL cache.
    Falls back to global settings for any key not overridden per workspace.
    """

    def __init__(self) -> None:
        self._cache: Dict[str, _CacheEntry] = {}
        self._lock = asyncio.Lock()

    def _cache_key(self, user_id: str, key: str) -> str:
        return f"{user_id}:{key}"

    async def get(self, user_id: str, key: str, default: Any = None) -> Any:
        ck = self._cache_key(user_id, key)
        now = time.monotonic()
        async with self._lock:
            if ck in self._cache:
                val, exp = self._cache[ck]
                if now < exp:
                    return val
            val = await self._fetch(user_id, key)
            if val is None:
                val = default if default is not None else _get_system_defaults().get(key)
            self._cache[ck] = (val, now + _CACHE_TTL)
            return val

    async def get_all(self, user_id: str) -> Dict[str, Any]:
        """Return merged dict: system defaults overridden by workspace config."""
        defaults = _get_system_defaults()
        async with async_session_factory() as db:
            result = await db.execute(
                select(WorkspaceRuntimeConfig).where(
                    WorkspaceRuntimeConfig.user_id == user_id
                )
            )
            rows = result.scalars().all()
        workspace_vals = {}
        for row in rows:
            try:
                workspace_vals[row.key] = json.loads(row.value)
            except json.JSONDecodeError:
                pass
        return {**defaults, **workspace_vals}

    async def set(self, user_id: str, key: str, value: Any) -> None:
        json_val = json.dumps(value)
        async with async_session_factory() as db:
            result = await db.execute(
                select(WorkspaceRuntimeConfig).where(
                    WorkspaceRuntimeConfig.user_id == user_id,
                    WorkspaceRuntimeConfig.key == key,
                )
            )
            row = result.scalar_one_or_none()
            if row is None:
                db.add(WorkspaceRuntimeConfig(user_id=user_id, key=key, value=json_val))
            else:
                row.value = json_val
            await db.commit()
        # Invalidate cache
        ck = self._cache_key(user_id, key)
        async with self._lock:
            self._cache.pop(ck, None)

    async def bulk_update(self, user_id: str, updates: Dict[str, Any]) -> None:
        for key, value in updates.items():
            await self.set(user_id, key, value)

    async def _fetch(self, user_id: str, key: str) -> Optional[Any]:
        async with async_session_factory() as db:
            result = await db.execute(
                select(WorkspaceRuntimeConfig).where(
                    WorkspaceRuntimeConfig.user_id == user_id,
                    WorkspaceRuntimeConfig.key == key,
                )
            )
            row = result.scalar_one_or_none()
        if row is None:
            return None
        try:
            return json.loads(row.value)
        except json.JSONDecodeError:
            return None


_svc: WorkspaceRuntimeConfigService | None = None


def get_runtime_config_service() -> WorkspaceRuntimeConfigService:
    global _svc
    if _svc is None:
        _svc = WorkspaceRuntimeConfigService()
    return _svc


__all__ = ["WorkspaceRuntimeConfigService", "get_runtime_config_service"]
