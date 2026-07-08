"""
services/workspace/provider_service.py

CRUD operations for workspace_providers table.
Handles encryption/decryption of API keys and provider lifecycle.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.engine import async_session_factory
from db.models.workspace_settings import WorkspaceProvider
from services.encryption import decrypt, encrypt, mask

logger = logging.getLogger(__name__)

# ── Provider default config schemas ───────────────────────────────────────────

_PROVIDER_DEFAULTS: Dict[str, Dict[str, Any]] = {
    # LLM providers
    "groq": {"model": "llama-3.3-70b-versatile", "temperature": 0.2, "max_tokens": 2048, "streaming": True},
    "openai": {"model": "gpt-4o-mini", "temperature": 0.2, "max_tokens": 2048, "streaming": True},
    "anthropic": {"model": "claude-3-5-haiku-20241022", "temperature": 0.2, "max_tokens": 2048, "streaming": True},
    "gemini": {"model": "gemini-1.5-flash", "temperature": 0.2, "max_tokens": 2048, "streaming": True},
    "openrouter": {"model": "meta-llama/llama-3.1-8b-instruct:free", "temperature": 0.2, "max_tokens": 2048, "streaming": True},
    "deepseek": {"model": "deepseek-chat", "temperature": 0.2, "max_tokens": 2048, "streaming": True},
    "azure_openai": {"model": "gpt-4o", "temperature": 0.2, "max_tokens": 2048, "streaming": True, "endpoint": "", "api_version": "2024-02-01"},
    "ollama": {"model": "llama3.2", "temperature": 0.2, "max_tokens": 2048, "streaming": True, "endpoint": "http://localhost:11434"},
    # Embedding providers
    "cohere": {"model": "embed-english-v3.0", "dimensions": 1024},
    "openai_embed": {"model": "text-embedding-3-small", "dimensions": 1536},
    "voyage": {"model": "voyage-3-lite", "dimensions": 512},
    "jina": {"model": "jina-embeddings-v3", "dimensions": 1024},
    "mixedbread": {"model": "mxbai-embed-large-v1", "dimensions": 1024},
    "nomic": {"model": "nomic-embed-text-v1.5", "dimensions": 768},
    # Search providers
    "serper": {"max_results": 10, "timeout": 15},
    "tavily": {"max_results": 10, "timeout": 15},
    "brave": {"max_results": 10, "timeout": 15},
    "exa": {"max_results": 10, "timeout": 15},
    "duckduckgo": {"max_results": 10, "timeout": 15},
    "google_search": {"max_results": 10, "timeout": 15},
}


class ProviderService:
    """CRUD operations for workspace providers."""

    async def list_providers(
        self,
        user_id: str,
        provider_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List all providers for a user, optionally filtered by type."""
        async with async_session_factory() as db:
            q = select(WorkspaceProvider).where(WorkspaceProvider.user_id == user_id)
            if provider_type:
                q = q.where(WorkspaceProvider.provider_type == provider_type)
            result = await db.execute(q.order_by(WorkspaceProvider.created_at))
            rows = result.scalars().all()
        return [self._serialize(r) for r in rows]

    async def get_provider(self, user_id: str, provider_id: str) -> Optional[Dict[str, Any]]:
        async with async_session_factory() as db:
            result = await db.execute(
                select(WorkspaceProvider).where(
                    WorkspaceProvider.id == provider_id,
                    WorkspaceProvider.user_id == user_id,
                )
            )
            row = result.scalar_one_or_none()
        return self._serialize(row) if row else None

    async def create_provider(
        self,
        user_id: str,
        provider_type: str,
        provider_name: str,
        config: Dict[str, Any],
        display_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new provider, encrypting api_key in config."""
        defaults = _PROVIDER_DEFAULTS.get(provider_name, {})
        merged = {**defaults, **config}
        encrypted = self._encrypt_config(merged)

        async with async_session_factory() as db:
            row = WorkspaceProvider(
                user_id=user_id,
                provider_type=provider_type,
                provider_name=provider_name,
                display_name=display_name or provider_name.title(),
                config_json=json.dumps(encrypted),
                status="disconnected",
            )
            db.add(row)
            await db.commit()
            await db.refresh(row)
        return self._serialize(row)

    async def update_provider(
        self,
        user_id: str,
        provider_id: str,
        config: Dict[str, Any],
        display_name: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        async with async_session_factory() as db:
            result = await db.execute(
                select(WorkspaceProvider).where(
                    WorkspaceProvider.id == provider_id,
                    WorkspaceProvider.user_id == user_id,
                )
            )
            row = result.scalar_one_or_none()
            if not row:
                return None

            # Merge with existing (so partial updates preserve existing keys)
            existing = self._decrypt_config(json.loads(row.config_json))
            merged = {**existing, **config}
            encrypted = self._encrypt_config(merged)
            row.config_json = json.dumps(encrypted)
            row.status = "disconnected"  # re-validate after config change
            if display_name:
                row.display_name = display_name
            await db.commit()
            await db.refresh(row)
        return self._serialize(row)

    async def delete_provider(self, user_id: str, provider_id: str) -> bool:
        async with async_session_factory() as db:
            result = await db.execute(
                select(WorkspaceProvider).where(
                    WorkspaceProvider.id == provider_id,
                    WorkspaceProvider.user_id == user_id,
                )
            )
            row = result.scalar_one_or_none()
            if not row:
                return False
            await db.delete(row)
            await db.commit()
        return True

    async def set_default(self, user_id: str, provider_id: str, provider_type: str) -> bool:
        """Set provider as default, clearing any previous default of same type."""
        async with async_session_factory() as db:
            # Clear existing defaults for this provider_type
            await db.execute(
                update(WorkspaceProvider)
                .where(
                    WorkspaceProvider.user_id == user_id,
                    WorkspaceProvider.provider_type == provider_type,
                )
                .values(is_default=False)
            )
            # Set new default
            result = await db.execute(
                select(WorkspaceProvider).where(
                    WorkspaceProvider.id == provider_id,
                    WorkspaceProvider.user_id == user_id,
                )
            )
            row = result.scalar_one_or_none()
            if not row:
                return False
            row.is_default = True
            await db.commit()
        return True

    async def set_fallback(self, user_id: str, provider_id: str, provider_type: str) -> bool:
        """Set provider as fallback, clearing any previous fallback of same type."""
        async with async_session_factory() as db:
            await db.execute(
                update(WorkspaceProvider)
                .where(
                    WorkspaceProvider.user_id == user_id,
                    WorkspaceProvider.provider_type == provider_type,
                )
                .values(is_fallback=False)
            )
            result = await db.execute(
                select(WorkspaceProvider).where(
                    WorkspaceProvider.id == provider_id,
                    WorkspaceProvider.user_id == user_id,
                )
            )
            row = result.scalar_one_or_none()
            if not row:
                return False
            row.is_fallback = True
            await db.commit()
        return True

    async def update_status(
        self,
        provider_id: str,
        status: str,
        health_status: Optional[str] = None,
        latency_ms: Optional[float] = None,
        error: Optional[str] = None,
    ) -> None:
        from datetime import datetime, timezone
        async with async_session_factory() as db:
            result = await db.execute(
                select(WorkspaceProvider).where(WorkspaceProvider.id == provider_id)
            )
            row = result.scalar_one_or_none()
            if row:
                row.status = status
                row.health_status = health_status
                row.latency_ms = latency_ms
                row.last_error = error
                row.last_validated_at = datetime.now(timezone.utc)
                await db.commit()

    def get_decrypted_config(self, provider: Dict[str, Any]) -> Dict[str, Any]:
        """Return config with api_key decrypted. For internal use only."""
        return provider.get("_decrypted_config", {})

    # ── Serialization ──────────────────────────────────────────────────────────

    def _serialize(self, row: WorkspaceProvider) -> Dict[str, Any]:
        """Serialize a DB row for the API response. Masks the API key."""
        try:
            raw_config = json.loads(row.config_json)
            decrypted = self._decrypt_config(raw_config)
        except Exception:
            decrypted = {}

        # For API responses: mask API key, exclude secrets
        public_config = {k: (mask(v) if k == "api_key" and v else v) for k, v in decrypted.items()}

        return {
            "id": row.id,
            "user_id": row.user_id,
            "provider_type": row.provider_type,
            "provider_name": row.provider_name,
            "display_name": row.display_name,
            "config": public_config,
            "is_default": row.is_default,
            "is_fallback": row.is_fallback,
            "status": row.status,
            "health_status": row.health_status,
            "last_validated_at": row.last_validated_at.isoformat() if row.last_validated_at else None,
            "latency_ms": row.latency_ms,
            "last_error": row.last_error,
            "created_at": row.created_at.isoformat() if row.created_at else None,
            # Internal decrypted config attached for factory use, NOT sent to clients
            "_decrypted_config": decrypted,
        }

    def _encrypt_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt api_key inside config dict."""
        result = dict(config)
        if "api_key" in result and result["api_key"]:
            result["api_key"] = encrypt(result["api_key"])
            result["api_key_encrypted"] = True
        return result

    def _decrypt_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt api_key inside config dict."""
        result = dict(config)
        if result.get("api_key_encrypted") and result.get("api_key"):
            result["api_key"] = decrypt(result["api_key"])
            result.pop("api_key_encrypted", None)
        return result


# Module-level singleton
_svc: ProviderService | None = None


def get_provider_service() -> ProviderService:
    global _svc
    if _svc is None:
        _svc = ProviderService()
    return _svc


__all__ = ["ProviderService", "get_provider_service"]
