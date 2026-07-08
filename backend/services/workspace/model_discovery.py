"""
services/workspace/model_discovery.py

Fetches available models from provider APIs.
Results are cached in the workspace_models table (1-hour TTL).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

import httpx
from sqlalchemy import select, delete

from db.engine import async_session_factory
from db.models.workspace_settings import WorkspaceModel

logger = logging.getLogger(__name__)

_CACHE_TTL_HOURS = 1
_TIMEOUT = 20.0

# ── Static model catalogs for providers with no list API ──────────────────────

_ANTHROPIC_MODELS = [
    {"model_id": "claude-opus-4-5", "model_name": "Claude Opus 4.5", "context_window": 200000,
     "supports_streaming": True, "supports_vision": True, "supports_function_calling": True, "is_recommended": True},
    {"model_id": "claude-sonnet-4-5", "model_name": "Claude Sonnet 4.5", "context_window": 200000,
     "supports_streaming": True, "supports_vision": True, "supports_function_calling": True, "is_recommended": True},
    {"model_id": "claude-3-5-haiku-20241022", "model_name": "Claude 3.5 Haiku", "context_window": 200000,
     "supports_streaming": True, "supports_vision": True, "supports_function_calling": True, "is_recommended": False},
    {"model_id": "claude-3-opus-20240229", "model_name": "Claude 3 Opus", "context_window": 200000,
     "supports_streaming": True, "supports_vision": True, "supports_function_calling": True, "is_recommended": False},
]

_GEMINI_MODELS = [
    {"model_id": "gemini-2.0-flash", "model_name": "Gemini 2.0 Flash", "context_window": 1048576,
     "supports_streaming": True, "supports_vision": True, "supports_function_calling": True, "is_recommended": True},
    {"model_id": "gemini-1.5-pro", "model_name": "Gemini 1.5 Pro", "context_window": 2097152,
     "supports_streaming": True, "supports_vision": True, "supports_function_calling": True, "is_recommended": True},
    {"model_id": "gemini-1.5-flash", "model_name": "Gemini 1.5 Flash", "context_window": 1048576,
     "supports_streaming": True, "supports_vision": True, "supports_function_calling": True, "is_recommended": False},
]

_DEEPSEEK_MODELS = [
    {"model_id": "deepseek-chat", "model_name": "DeepSeek Chat V3", "context_window": 65536,
     "supports_streaming": True, "supports_vision": False, "supports_function_calling": True, "is_recommended": True},
    {"model_id": "deepseek-reasoner", "model_name": "DeepSeek Reasoner (R1)", "context_window": 65536,
     "supports_streaming": True, "supports_vision": False, "supports_function_calling": False, "supports_reasoning": True, "is_recommended": True},
]


class ModelDiscoveryService:

    async def get_models(self, user_id: str, provider_name: str, api_key: str = "", endpoint: str = "") -> List[Dict[str, Any]]:
        """
        Return models for a provider, using cache if fresh.
        Falls back to static catalog if API is unavailable.
        """
        # Check DB cache first
        cached = await self._get_cached(user_id, provider_name)
        if cached:
            return cached

        # Fetch from provider API
        try:
            models = await self._fetch_models(provider_name, api_key, endpoint)
        except Exception as exc:
            logger.warning("Model discovery failed for %s: %s", provider_name, exc)
            models = self._static_catalog(provider_name)

        # Persist to DB cache
        if models:
            await self._persist(user_id, provider_name, models)

        return models

    async def _get_cached(self, user_id: str, provider_name: str) -> Optional[List[Dict[str, Any]]]:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=_CACHE_TTL_HOURS)
        async with async_session_factory() as db:
            result = await db.execute(
                select(WorkspaceModel).where(
                    WorkspaceModel.user_id == user_id,
                    WorkspaceModel.provider_name == provider_name,
                    WorkspaceModel.last_fetched_at > cutoff,
                ).order_by(WorkspaceModel.model_name)
            )
            rows = result.scalars().all()
        if not rows:
            return None
        return [self._row_to_dict(r) for r in rows]

    async def _persist(self, user_id: str, provider_name: str, models: List[Dict[str, Any]]) -> None:
        async with async_session_factory() as db:
            # Delete stale entries
            await db.execute(
                delete(WorkspaceModel).where(
                    WorkspaceModel.user_id == user_id,
                    WorkspaceModel.provider_name == provider_name,
                )
            )
            now = datetime.now(timezone.utc)
            for m in models:
                db.add(WorkspaceModel(
                    user_id=user_id,
                    provider_name=provider_name,
                    model_id=m.get("model_id", ""),
                    model_name=m.get("model_name", m.get("model_id", "")),
                    context_window=m.get("context_window"),
                    input_cost_per_1m=m.get("input_cost_per_1m"),
                    output_cost_per_1m=m.get("output_cost_per_1m"),
                    supports_streaming=m.get("supports_streaming", True),
                    supports_vision=m.get("supports_vision", False),
                    supports_json_mode=m.get("supports_json_mode", False),
                    supports_function_calling=m.get("supports_function_calling", False),
                    supports_reasoning=m.get("supports_reasoning", False),
                    is_recommended=m.get("is_recommended", False),
                    last_fetched_at=now,
                ))
            await db.commit()

    async def _fetch_models(self, provider_name: str, api_key: str, endpoint: str) -> List[Dict[str, Any]]:
        if provider_name == "groq":
            return await self._fetch_openai_compat(api_key, "https://api.groq.com/openai/v1/models")
        elif provider_name == "openai":
            return await self._fetch_openai_compat(api_key, "https://api.openai.com/v1/models")
        elif provider_name == "openrouter":
            return await self._fetch_openrouter(api_key)
        elif provider_name == "gemini":
            return await self._fetch_gemini(api_key)
        elif provider_name == "anthropic":
            return _ANTHROPIC_MODELS
        elif provider_name == "deepseek":
            return _DEEPSEEK_MODELS
        elif provider_name == "ollama":
            return await self._fetch_ollama(endpoint or "http://localhost:11434")
        elif provider_name == "azure_openai":
            return []  # Azure models are deployment-specific
        return self._static_catalog(provider_name)

    async def _fetch_openai_compat(self, api_key: str, url: str) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            r = await client.get(url, headers={"Authorization": f"Bearer {api_key}"})
        r.raise_for_status()
        data = r.json().get("data", [])
        return [
            {
                "model_id": m["id"],
                "model_name": m.get("display_name", m["id"]),
                "context_window": m.get("context_window"),
                "supports_streaming": True,
                "supports_vision": any(k in m["id"].lower() for k in ["vision", "gpt-4o", "gemini"]),
                "supports_function_calling": True,
                "is_recommended": any(k in m["id"].lower() for k in ["llama-3.3", "llama3.3", "gpt-4o-mini"]),
            }
            for m in data
            if not m["id"].startswith("whisper") and not m["id"].startswith("tts")
        ]

    async def _fetch_openrouter(self, api_key: str) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            r = await client.get(
                "https://openrouter.ai/api/v1/models",
                headers={"Authorization": f"Bearer {api_key}"},
            )
        r.raise_for_status()
        data = r.json().get("data", [])
        return [
            {
                "model_id": m["id"],
                "model_name": m.get("name", m["id"]),
                "context_window": m.get("context_length"),
                "input_cost_per_1m": float(m.get("pricing", {}).get("prompt", 0)) * 1_000_000,
                "output_cost_per_1m": float(m.get("pricing", {}).get("completion", 0)) * 1_000_000,
                "supports_streaming": True,
                "is_recommended": ":free" in m["id"],
            }
            for m in data[:100]  # cap at 100 for performance
        ]

    async def _fetch_gemini(self, api_key: str) -> List[Dict[str, Any]]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            r = await client.get(url)
        if r.status_code != 200:
            return _GEMINI_MODELS
        data = r.json().get("models", [])
        return [
            {
                "model_id": m["name"].replace("models/", ""),
                "model_name": m.get("displayName", m["name"]),
                "context_window": m.get("inputTokenLimit"),
                "supports_streaming": True,
                "supports_vision": "vision" in m.get("displayName", "").lower() or "flash" in m.get("name", "").lower(),
                "is_recommended": "flash" in m["name"].lower() or "pro" in m["name"].lower(),
            }
            for m in data
            if "generateContent" in m.get("supportedGenerationMethods", [])
        ]

    async def _fetch_ollama(self, endpoint: str) -> List[Dict[str, Any]]:
        url = f"{endpoint.rstrip('/')}/api/tags"
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            r = await client.get(url)
        r.raise_for_status()
        models = r.json().get("models", [])
        return [
            {
                "model_id": m["name"],
                "model_name": m["name"],
                "context_window": None,
                "supports_streaming": True,
                "is_local": True,
            }
            for m in models
        ]

    def _static_catalog(self, provider_name: str) -> List[Dict[str, Any]]:
        catalogs = {
            "anthropic": _ANTHROPIC_MODELS,
            "gemini": _GEMINI_MODELS,
            "deepseek": _DEEPSEEK_MODELS,
        }
        return catalogs.get(provider_name, [])

    def _row_to_dict(self, row: WorkspaceModel) -> Dict[str, Any]:
        return {
            "id": row.id,
            "model_id": row.model_id,
            "model_name": row.model_name,
            "provider_name": row.provider_name,
            "context_window": row.context_window,
            "input_cost_per_1m": row.input_cost_per_1m,
            "output_cost_per_1m": row.output_cost_per_1m,
            "supports_streaming": row.supports_streaming,
            "supports_vision": row.supports_vision,
            "supports_json_mode": row.supports_json_mode,
            "supports_function_calling": row.supports_function_calling,
            "supports_reasoning": row.supports_reasoning,
            "is_recommended": row.is_recommended,
            "is_default": row.is_default,
            "is_favorite": row.is_favorite,
            "last_fetched_at": row.last_fetched_at.isoformat() if row.last_fetched_at else None,
        }

    async def toggle_favorite(self, user_id: str, model_id_pk: str) -> bool:
        async with async_session_factory() as db:
            result = await db.execute(
                select(WorkspaceModel).where(
                    WorkspaceModel.id == model_id_pk,
                    WorkspaceModel.user_id == user_id,
                )
            )
            row = result.scalar_one_or_none()
            if not row:
                return False
            row.is_favorite = not row.is_favorite
            await db.commit()
        return True

    async def set_default_model(self, user_id: str, model_id_pk: str, provider_name: str) -> bool:
        from sqlalchemy import update
        async with async_session_factory() as db:
            await db.execute(
                update(WorkspaceModel)
                .where(WorkspaceModel.user_id == user_id, WorkspaceModel.provider_name == provider_name)
                .values(is_default=False)
            )
            result = await db.execute(
                select(WorkspaceModel).where(
                    WorkspaceModel.id == model_id_pk,
                    WorkspaceModel.user_id == user_id,
                )
            )
            row = result.scalar_one_or_none()
            if not row:
                return False
            row.is_default = True
            await db.commit()
        return True


_svc: ModelDiscoveryService | None = None


def get_model_discovery() -> ModelDiscoveryService:
    global _svc
    if _svc is None:
        _svc = ModelDiscoveryService()
    return _svc


__all__ = ["ModelDiscoveryService", "get_model_discovery"]
