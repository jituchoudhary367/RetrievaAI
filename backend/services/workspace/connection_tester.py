"""
services/workspace/connection_tester.py

Async connection tester for all provider types.
Makes a minimal, low-cost API call to verify credentials and measure latency.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger(__name__)

_TIMEOUT = 15.0  # seconds


async def test_llm_connection(provider_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Test an LLM provider connection.
    Returns {success, latency_ms, model_count, error}.
    """
    api_key = config.get("api_key", "")
    t0 = time.monotonic()
    try:
        if provider_name == "groq":
            return await _test_openai_compat(
                api_key, "https://api.groq.com/openai/v1/models", t0
            )
        elif provider_name == "openai":
            return await _test_openai_compat(
                api_key, "https://api.openai.com/v1/models", t0
            )
        elif provider_name == "anthropic":
            return await _test_anthropic(api_key, t0)
        elif provider_name == "gemini":
            return await _test_gemini(api_key, t0)
        elif provider_name == "openrouter":
            return await _test_openai_compat(
                api_key, "https://openrouter.ai/api/v1/models", t0
            )
        elif provider_name == "deepseek":
            return await _test_openai_compat(
                api_key, "https://api.deepseek.com/v1/models", t0
            )
        elif provider_name == "azure_openai":
            endpoint = config.get("endpoint", "")
            api_version = config.get("api_version", "2024-02-01")
            if not endpoint:
                return {"success": False, "error": "Endpoint URL is required for Azure OpenAI", "latency_ms": 0}
            url = f"{endpoint.rstrip('/')}/openai/deployments?api-version={api_version}"
            return await _test_azure(api_key, url, t0)
        elif provider_name == "ollama":
            endpoint = config.get("endpoint", "http://localhost:11434")
            return await _test_ollama(endpoint, t0)
        else:
            return {"success": False, "error": f"Unknown provider: {provider_name}", "latency_ms": 0}
    except Exception as exc:
        return {"success": False, "error": str(exc), "latency_ms": int((time.monotonic() - t0) * 1000)}


async def test_embedding_connection(provider_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Test an embedding provider connection."""
    api_key = config.get("api_key", "")
    model = config.get("model", "")
    t0 = time.monotonic()
    try:
        if provider_name in ("cohere", "cohere_embed"):
            return await _test_cohere_embed(api_key, model, t0)
        elif provider_name in ("openai", "openai_embed"):
            return await _test_openai_embed(api_key, model, t0)
        elif provider_name in ("ollama", "ollama_embed"):
            endpoint = config.get("endpoint", "http://localhost:11434")
            return await _test_ollama_embed(endpoint, model, t0)
        elif provider_name in ("huggingface", "local"):
            return {"success": True, "latency_ms": 0, "note": "Local model — no connection test needed"}
        else:
            # For cloud providers without a test endpoint, just validate the key format
            if api_key:
                return {"success": True, "latency_ms": int((time.monotonic() - t0) * 1000), "note": "Key provided"}
            return {"success": False, "error": "API key is required", "latency_ms": 0}
    except Exception as exc:
        return {"success": False, "error": str(exc), "latency_ms": int((time.monotonic() - t0) * 1000)}


async def test_search_connection(provider_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Test a search provider connection."""
    api_key = config.get("api_key", "")
    t0 = time.monotonic()
    try:
        if provider_name == "duckduckgo":
            return {"success": True, "latency_ms": 0, "note": "DuckDuckGo requires no API key"}
        elif provider_name == "serper":
            return await _test_serper(api_key, t0)
        elif provider_name == "tavily":
            return await _test_tavily(api_key, t0)
        elif provider_name == "brave":
            return await _test_brave(api_key, t0)
        else:
            if api_key:
                return {"success": True, "latency_ms": int((time.monotonic() - t0) * 1000)}
            return {"success": False, "error": "API key is required", "latency_ms": 0}
    except Exception as exc:
        return {"success": False, "error": str(exc), "latency_ms": int((time.monotonic() - t0) * 1000)}


# ── Internal helpers ───────────────────────────────────────────────────────────

async def _test_openai_compat(api_key: str, url: str, t0: float) -> Dict[str, Any]:
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        r = await client.get(url, headers={"Authorization": f"Bearer {api_key}"})
    latency = int((time.monotonic() - t0) * 1000)
    if r.status_code == 200:
        data = r.json()
        count = len(data.get("data", []))
        return {"success": True, "latency_ms": latency, "model_count": count}
    return {"success": False, "error": f"HTTP {r.status_code}: {r.text[:200]}", "latency_ms": latency}


async def _test_anthropic(api_key: str, t0: float) -> Dict[str, Any]:
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        r = await client.get(
            "https://api.anthropic.com/v1/models",
            headers={"x-api-key": api_key, "anthropic-version": "2023-06-01"},
        )
    latency = int((time.monotonic() - t0) * 1000)
    if r.status_code == 200:
        return {"success": True, "latency_ms": latency}
    return {"success": False, "error": f"HTTP {r.status_code}: {r.text[:200]}", "latency_ms": latency}


async def _test_gemini(api_key: str, t0: float) -> Dict[str, Any]:
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        r = await client.get(url)
    latency = int((time.monotonic() - t0) * 1000)
    if r.status_code == 200:
        return {"success": True, "latency_ms": latency}
    return {"success": False, "error": f"HTTP {r.status_code}: {r.text[:200]}", "latency_ms": latency}


async def _test_azure(api_key: str, url: str, t0: float) -> Dict[str, Any]:
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        r = await client.get(url, headers={"api-key": api_key})
    latency = int((time.monotonic() - t0) * 1000)
    if r.status_code == 200:
        return {"success": True, "latency_ms": latency}
    return {"success": False, "error": f"HTTP {r.status_code}: {r.text[:200]}", "latency_ms": latency}


async def _test_ollama(endpoint: str, t0: float) -> Dict[str, Any]:
    url = f"{endpoint.rstrip('/')}/api/tags"
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        r = await client.get(url)
    latency = int((time.monotonic() - t0) * 1000)
    if r.status_code == 200:
        models = r.json().get("models", [])
        return {"success": True, "latency_ms": latency, "model_count": len(models)}
    return {"success": False, "error": f"Ollama not reachable at {endpoint}", "latency_ms": latency}


async def _test_cohere_embed(api_key: str, model: str, t0: float) -> Dict[str, Any]:
    model = model or "embed-english-v3.0"
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        r = await client.post(
            "https://api.cohere.com/v2/embed",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"texts": ["test"], "model": model, "input_type": "search_query"},
        )
    latency = int((time.monotonic() - t0) * 1000)
    if r.status_code == 200:
        dims = len(r.json().get("embeddings", {}).get("float", [[]])[0])
        return {"success": True, "latency_ms": latency, "dimensions": dims}
    return {"success": False, "error": f"HTTP {r.status_code}: {r.text[:200]}", "latency_ms": latency}


async def _test_openai_embed(api_key: str, model: str, t0: float) -> Dict[str, Any]:
    model = model or "text-embedding-3-small"
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        r = await client.post(
            "https://api.openai.com/v1/embeddings",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"input": "test", "model": model},
        )
    latency = int((time.monotonic() - t0) * 1000)
    if r.status_code == 200:
        dims = len(r.json()["data"][0]["embedding"])
        return {"success": True, "latency_ms": latency, "dimensions": dims}
    return {"success": False, "error": f"HTTP {r.status_code}: {r.text[:200]}", "latency_ms": latency}


async def _test_ollama_embed(endpoint: str, model: str, t0: float) -> Dict[str, Any]:
    model = model or "nomic-embed-text"
    url = f"{endpoint.rstrip('/')}/api/embeddings"
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        r = await client.post(url, json={"model": model, "prompt": "test"})
    latency = int((time.monotonic() - t0) * 1000)
    if r.status_code == 200:
        dims = len(r.json().get("embedding", []))
        return {"success": True, "latency_ms": latency, "dimensions": dims}
    return {"success": False, "error": f"HTTP {r.status_code}: {r.text[:200]}", "latency_ms": latency}


async def _test_serper(api_key: str, t0: float) -> Dict[str, Any]:
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        r = await client.post(
            "https://google.serper.dev/search",
            headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
            json={"q": "test"},
        )
    latency = int((time.monotonic() - t0) * 1000)
    if r.status_code == 200:
        return {"success": True, "latency_ms": latency}
    return {"success": False, "error": f"HTTP {r.status_code}: {r.text[:200]}", "latency_ms": latency}


async def _test_tavily(api_key: str, t0: float) -> Dict[str, Any]:
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        r = await client.post(
            "https://api.tavily.com/search",
            headers={"Content-Type": "application/json"},
            json={"api_key": api_key, "query": "test", "max_results": 1},
        )
    latency = int((time.monotonic() - t0) * 1000)
    if r.status_code == 200:
        return {"success": True, "latency_ms": latency}
    return {"success": False, "error": f"HTTP {r.status_code}: {r.text[:200]}", "latency_ms": latency}


async def _test_brave(api_key: str, t0: float) -> Dict[str, Any]:
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        r = await client.get(
            "https://api.search.brave.com/res/v1/web/search",
            headers={"Accept": "application/json", "X-Subscription-Token": api_key},
            params={"q": "test", "count": 1},
        )
    latency = int((time.monotonic() - t0) * 1000)
    if r.status_code == 200:
        return {"success": True, "latency_ms": latency}
    return {"success": False, "error": f"HTTP {r.status_code}: {r.text[:200]}", "latency_ms": latency}


__all__ = ["test_llm_connection", "test_embedding_connection", "test_search_connection"]
