"""
services/user_preferences.py

User-scoped settings that persist in Postgres.
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
from db.models.settings import UserPreference

logger = logging.getLogger(__name__)

_CacheEntry = Tuple[Any, float]
_CACHE_TTL_SECONDS = 60.0


class UserPreferencesService:
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
                value, expires = self._cache[ck]
                if now < expires:
                    return value
            
            value = await self._fetch(user_id, key, default)
            self._cache[ck] = (value, now + _CACHE_TTL_SECONDS)
            return value

    async def set(self, user_id: str, key: str, value: Any) -> None:
        json_value = json.dumps(value)
        async with async_session_factory() as db:
            result = await db.execute(
                select(UserPreference).where(
                    UserPreference.user_id == user_id,
                    UserPreference.key == key,
                )
            )
            row = result.scalar_one_or_none()
            if row is None:
                db.add(UserPreference(
                    user_id=user_id,
                    key=key,
                    value=json_value,
                ))
            else:
                row.value = json_value
            await db.commit()

        ck = self._cache_key(user_id, key)
        async with self._lock:
            self._cache.pop(ck, None)

    async def get_all_for_user(self, user_id: str) -> Dict[str, Any]:
        async with async_session_factory() as db:
            result = await db.execute(
                select(UserPreference).where(UserPreference.user_id == user_id)
            )
            rows = result.scalars().all()
        return {row.key: json.loads(row.value) for row in rows}

    async def _fetch(self, user_id: str, key: str, default: Any) -> Any:
        async with async_session_factory() as db:
            result = await db.execute(
                select(UserPreference).where(
                    UserPreference.user_id == user_id,
                    UserPreference.key == key,
                )
            )
            row = result.scalar_one_or_none()
        if row is None:
            return default
        try:
            return json.loads(row.value)
        except json.JSONDecodeError:
            logger.warning("UserPreference: could not JSON-decode value for %s", key)
            return default


_svc: UserPreferencesService | None = None

def get_user_preferences() -> UserPreferencesService:
    global _svc
    if _svc is None:
        _svc = UserPreferencesService()
    return _svc

__all__ = ["UserPreferencesService", "get_user_preferences"]
