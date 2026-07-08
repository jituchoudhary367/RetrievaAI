"""
services/workspace/provider_factory.py

The central resolution layer for workspace-scoped providers.

Resolution order for each resource type:
  1. Workspace default provider (from workspace_providers table)
  2. If none: fall back to global get_settings() defaults

This is the ONLY file that the existing pipeline touches.
The rag_pipeline.py calls resolve_llm_for_user() before LLM generation.
Everything else remains untouched.

Circuit breaker: if a provider fails 3 consecutive times within 60 seconds,
automatically switch to the workspace's fallback provider (or global default).
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Circuit breaker state: provider_id → (failure_count, first_failure_at)
_circuit_breaker: Dict[str, tuple] = {}
_CB_MAX_FAILURES = 3
_CB_WINDOW_SECONDS = 60


def _is_tripped(provider_id: str) -> bool:
    if provider_id not in _circuit_breaker:
        return False
    failures, first_at = _circuit_breaker[provider_id]
    if time.monotonic() - first_at > _CB_WINDOW_SECONDS:
        # Reset after window
        del _circuit_breaker[provider_id]
        return False
    return failures >= _CB_MAX_FAILURES


def record_provider_failure(provider_id: str) -> None:
    if provider_id not in _circuit_breaker:
        _circuit_breaker[provider_id] = (1, time.monotonic())
    else:
        failures, first_at = _circuit_breaker[provider_id]
        _circuit_breaker[provider_id] = (failures + 1, first_at)


def record_provider_success(provider_id: str) -> None:
    _circuit_breaker.pop(provider_id, None)


async def resolve_llm_for_user(
    user_id: str,
    user_api_keys: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Resolve the LLM configuration for a user's workspace.

    Returns a dict with keys:
      provider, model, api_key, base_url, temperature, max_tokens,
      streaming, timeout, azure_endpoint, azure_api_version
    """
    user_api_keys = user_api_keys or {}

    # 1. Check workspace default provider
    try:
        ws_config = await _get_workspace_llm_config(user_id)
        if ws_config and not _is_tripped(ws_config.get("provider_id", "")):
            # Merge with user_api_keys (user_api_keys take highest priority)
            api_key = user_api_keys.get("GROQ_API_KEY") or ws_config.get("api_key", "")
            return {
                **ws_config,
                "api_key": api_key,
            }
    except Exception as exc:
        logger.warning("Could not resolve workspace LLM config for %s: %s", user_id, exc)

    # 2. Fall back to global settings + user_api_keys
    return _global_llm_config(user_api_keys)


async def resolve_embedding_for_user(user_id: str) -> Dict[str, Any]:
    """
    Resolve the embedding configuration for a user's workspace.

    Returns a dict with keys:
      provider, model, api_key, dimensions, batch_size, normalize
    """
    try:
        ws_config = await _get_workspace_embedding_config(user_id)
        if ws_config:
            return ws_config
    except Exception as exc:
        logger.warning("Could not resolve workspace embedding config for %s: %s", user_id, exc)

    return _global_embedding_config()


async def resolve_search_for_user(user_id: str) -> Dict[str, Any]:
    """
    Resolve the search provider configuration for a user's workspace.

    Returns a dict with keys:
      provider, api_key, max_results, timeout
    """
    try:
        ws_config = await _get_workspace_search_config(user_id)
        if ws_config:
            return ws_config
    except Exception as exc:
        logger.warning("Could not resolve workspace search config for %s: %s", user_id, exc)

    return _global_search_config()


# ── Internal resolvers ─────────────────────────────────────────────────────────

async def _get_workspace_llm_config(user_id: str) -> Optional[Dict[str, Any]]:
    from services.workspace.provider_service import get_provider_service
    svc = get_provider_service()
    providers = await svc.list_providers(user_id, provider_type="llm")
    if not providers:
        return None

    # Find the default provider; if none marked default, use first
    default = next((p for p in providers if p["is_default"] and p["status"] == "connected"), None)
    if not default:
        default = next((p for p in providers if p["status"] == "connected"), None)
    if not default:
        return None

    decrypted = svc.get_decrypted_config(default)
    provider_name = default["provider_name"]

    return {
        "provider_id": default["id"],
        "provider": provider_name,
        "model": decrypted.get("model", ""),
        "api_key": decrypted.get("api_key", ""),
        "base_url": _get_base_url(provider_name, decrypted),
        "temperature": decrypted.get("temperature", 0.2),
        "max_tokens": decrypted.get("max_tokens", 2048),
        "streaming": decrypted.get("streaming", True),
        "timeout": decrypted.get("timeout", 60.0),
        "azure_endpoint": decrypted.get("endpoint") if provider_name == "azure_openai" else None,
        "azure_api_version": decrypted.get("api_version") if provider_name == "azure_openai" else None,
    }


async def _get_workspace_embedding_config(user_id: str) -> Optional[Dict[str, Any]]:
    from services.workspace.provider_service import get_provider_service
    svc = get_provider_service()
    providers = await svc.list_providers(user_id, provider_type="embedding")
    if not providers:
        return None

    default = next((p for p in providers if p["is_default"] and p["status"] == "connected"), None)
    if not default:
        default = next((p for p in providers if p["status"] == "connected"), None)
    if not default:
        return None

    decrypted = svc.get_decrypted_config(default)
    return {
        "provider_id": default["id"],
        "provider": default["provider_name"],
        "model": decrypted.get("model", ""),
        "api_key": decrypted.get("api_key", ""),
        "dimensions": decrypted.get("dimensions", 1024),
        "batch_size": decrypted.get("batch_size", 64),
        "normalize": decrypted.get("normalize", True),
    }


async def _get_workspace_search_config(user_id: str) -> Optional[Dict[str, Any]]:
    from services.workspace.provider_service import get_provider_service
    svc = get_provider_service()
    providers = await svc.list_providers(user_id, provider_type="search")
    if not providers:
        return None

    default = next((p for p in providers if p["is_default"]), None)
    if not default:
        default = providers[0]

    decrypted = svc.get_decrypted_config(default)
    return {
        "provider_id": default["id"],
        "provider": default["provider_name"],
        "api_key": decrypted.get("api_key", ""),
        "max_results": decrypted.get("max_results", 10),
        "timeout": decrypted.get("timeout", 15),
    }


def _get_base_url(provider_name: str, config: Dict[str, Any]) -> Optional[str]:
    base_urls = {
        "groq": "https://api.groq.com/openai/v1",
        "openrouter": "https://openrouter.ai/api/v1",
        "deepseek": "https://api.deepseek.com/v1",
        "ollama": config.get("endpoint", "http://localhost:11434") + "/v1",
    }
    if provider_name == "azure_openai":
        endpoint = config.get("endpoint", "")
        version = config.get("api_version", "2024-02-01")
        return f"{endpoint}/openai" if endpoint else None
    return base_urls.get(provider_name)


def _global_llm_config(user_api_keys: Dict[str, str]) -> Dict[str, Any]:
    from app.config import get_settings
    cfg = get_settings()
    api_key = (
        user_api_keys.get("GROQ_API_KEY")
        or user_api_keys.get("LLM_API_KEY")
        or cfg.resolved_llm_api_key()
    )
    return {
        "provider_id": None,
        "provider": cfg.llm.provider.value,
        "model": cfg.llm.model_name,
        "api_key": api_key,
        "base_url": cfg.resolved_llm_base_url(),
        "temperature": cfg.llm.temperature,
        "max_tokens": cfg.llm.max_tokens,
        "streaming": cfg.llm.streaming,
        "timeout": cfg.llm.timeout,
        "azure_endpoint": cfg.llm.azure_endpoint,
        "azure_api_version": cfg.llm.azure_api_version,
    }


def _global_embedding_config() -> Dict[str, Any]:
    from app.config import get_settings
    cfg = get_settings()
    return {
        "provider_id": None,
        "provider": cfg.embedding.provider.value,
        "model": cfg.embedding.model_name,
        "api_key": cfg.resolved_embedding_api_key(),
        "dimensions": cfg.embedding.dimensions,
        "batch_size": cfg.embedding.batch_size,
        "normalize": cfg.embedding.normalize,
    }


def _global_search_config() -> Dict[str, Any]:
    from app.config import get_settings
    cfg = get_settings()
    return {
        "provider_id": None,
        "provider": cfg.realtime_search.provider,
        "api_key": None,
        "max_results": 10,
        "timeout": cfg.realtime_search.timeout_seconds,
    }


__all__ = [
    "resolve_llm_for_user",
    "resolve_embedding_for_user",
    "resolve_search_for_user",
    "record_provider_failure",
    "record_provider_success",
]
