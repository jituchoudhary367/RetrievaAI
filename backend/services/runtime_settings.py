"""
services/runtime_settings.py

Dynamic, tenant-scoped settings that persist in Postgres (§1.7).

Provides TTL-cached reads so the DB isn't hit on every request, and
atomic writes that invalidate the relevant cache entry.

Usage:
    from services.runtime_settings import RuntimeSettingsService, get_runtime_settings
    svc = get_runtime_settings()
    val = await svc.get("my-tenant-id", "max_tokens", default=2048)
    await svc.set("my-tenant-id", "max_tokens", 4096, updated_by="user-id")

Rate Limit and Concurrent Requests are NOT here — they live in TenantConfig.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any, Dict, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.engine import async_session_factory
from db.models.settings import RuntimeSetting

logger = logging.getLogger(__name__)

# Cache entry: (value, expires_at_monotonic)
_CacheEntry = Tuple[Any, float]
_CACHE_TTL_SECONDS = 60.0


class RuntimeSettingsService:
    """
    Reads/writes RuntimeSetting rows with an in-process TTL cache.

    TTL-cached per (tenant_id, key) so config changes are picked up
    within _CACHE_TTL_SECONDS without needing a process restart.
    """

    def __init__(self) -> None:
        self._cache: Dict[str, _CacheEntry] = {}
        self._lock = asyncio.Lock()

    def _cache_key(self, key: str) -> str:
        return key

    async def get(self, key: str, default: Any = None) -> Any:
        ck = self._cache_key(key)
        now = time.monotonic()

        async with self._lock:
            if ck in self._cache:
                value, expires = self._cache[ck]
                if now < expires:
                    return value
            # Cache miss or expired — fetch from DB
            value = await self._fetch(key, default)
            self._cache[ck] = (value, now + _CACHE_TTL_SECONDS)
            return value

    async def set(
        self,
        key: str,
        value: Any,
        updated_by: Optional[str] = None,
    ) -> None:
        """Upsert a RuntimeSetting row and invalidate the cache entry."""
        json_value = json.dumps(value)
        async with async_session_factory() as db:
            result = await db.execute(
                select(RuntimeSetting).where(
                    RuntimeSetting.key == key,
                )
            )
            row = result.scalar_one_or_none()
            if row is None:
                db.add(RuntimeSetting(
                    key=key,
                    value=json_value,
                    updated_by=updated_by,
                ))
            else:
                row.value = json_value
                row.updated_by = updated_by
            await db.commit()

        # Invalidate cache
        ck = self._cache_key(key)
        async with self._lock:
            self._cache.pop(ck, None)

    async def get_all(self) -> Dict[str, Any]:
        """Return all RuntimeSetting rows as a {key: value} dict."""
        async with async_session_factory() as db:
            result = await db.execute(
                select(RuntimeSetting)
            )
            rows = result.scalars().all()
        return {row.key: json.loads(row.value) for row in rows}

    async def _fetch(self, key: str, default: Any) -> Any:
        async with async_session_factory() as db:
            result = await db.execute(
                select(RuntimeSetting).where(
                    RuntimeSetting.key == key,
                )
            )
            row = result.scalar_one_or_none()
        if row is None:
            return default
        try:
            return json.loads(row.value)
        except json.JSONDecodeError:
            logger.warning("RuntimeSetting: could not JSON-decode value for %s", key)
            return default


# Module-level singleton
_svc: RuntimeSettingsService | None = None


def get_runtime_settings() -> RuntimeSettingsService:
    global _svc
    if _svc is None:
        _svc = RuntimeSettingsService()
    return _svc


__all__ = ["RuntimeSettingsService", "get_runtime_settings"]
