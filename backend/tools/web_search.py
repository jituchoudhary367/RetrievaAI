"""
tools/web_search.py

Web search tool supporting Serper and Tavily APIs.

Graceful degradation:
  - Returns ``[]`` with a logged WARNING if no API key is configured
    (never raises in that case).
  - Raises ``WebSearchError`` only on actual API or network failures when
    a key IS configured.
  - ``httpx`` is lazily imported so the module is always importable.

Provider selection:
  - ``SERPER_API_KEY`` → Google Search via api.serper.dev
  - ``TAVILY_API_KEY`` → Tavily Search API
  - If both are set, Serper is preferred.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from app.config import get_settings

logger = logging.getLogger(__name__)


class WebSearchError(Exception):
    """Raised when a configured web search API call fails."""


class WebSearchTool:
    """
    Executes web searches via Serper or Tavily.

    Parameters
    ----------
    serper_api_key:
        Override the ``serper_api_key`` from settings (mainly for testing).
    tavily_api_key:
        Override the ``tavily_api_key`` from settings (mainly for testing).
    timeout:
        HTTP request timeout in seconds.
    """

    def __init__(
        self,
        serper_api_key: Optional[str] = None,
        tavily_api_key: Optional[str] = None,
        timeout: float = 15.0,
    ) -> None:
        settings = get_settings()
        self._serper_key: Optional[str] = serper_api_key or settings.serper_api_key
        self._tavily_key: Optional[str] = tavily_api_key or settings.tavily_api_key
        self._timeout = timeout

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def search(self, query: str, top_k: int = 5, tenant_id: Optional[str] = None) -> List[Dict]:
        """
        Search the web for *query* and return up to *top_k* results.

        Each result dict contains:
          ``title``   — page title
          ``url``     — page URL
          ``snippet`` — summary text

        Returns ``[]`` with a WARNING log when no API key is available
        (graceful degradation, not an exception).
        """
        import time
        import asyncio
        from services.tool_logger import log_tool_execution
        
        start_time = time.perf_counter()
        tool_id = "00000000-0000-0000-0001-000000000002"

        def _log(status: str, error: Optional[str] = None):
            if tenant_id:
                latency_ms = (time.perf_counter() - start_time) * 1000
                asyncio.create_task(log_tool_execution(
                    tenant_id=tenant_id,
                    tool_id=tool_id,
                    status=status,
                    latency_ms=latency_ms,
                    error_message=error
                ))

        try:
            if self._serper_key:
                res = self._search_serper(query, top_k)
                _log("success")
                return res
            if self._tavily_key:
                res = self._search_tavily(query, top_k)
                _log("success")
                return res
        except Exception as e:
            _log("failed", str(e))
            raise e

        logger.warning(
            "WebSearchTool: no SERPER_API_KEY or TAVILY_API_KEY configured — "
            "returning empty results. Set one of these environment variables "
            "to enable web search."
        )
        return []

    # ------------------------------------------------------------------
    # Serper backend
    # ------------------------------------------------------------------

    def _search_serper(self, query: str, top_k: int) -> List[Dict]:
        try:
            import httpx  # noqa: PLC0415
        except ImportError as exc:
            raise ImportError(
                "httpx is required for web search. "
                "Install it with: pip install httpx"
            ) from exc

        try:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.post(
                    "https://google.serper.dev/search",
                    headers={
                        "X-API-KEY": self._serper_key,
                        "Content-Type": "application/json",
                    },
                    json={"q": query, "num": top_k},
                )
                response.raise_for_status()
                data = response.json()
        except Exception as exc:
            raise WebSearchError(f"Serper API call failed: {exc}") from exc

        results: List[Dict] = []
        for item in data.get("organic", [])[:top_k]:
            results.append(
                {
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                }
            )
        logger.info("Serper returned %d results for query %r.", len(results), query)
        return results

    # ------------------------------------------------------------------
    # Tavily backend
    # ------------------------------------------------------------------

    def _search_tavily(self, query: str, top_k: int) -> List[Dict]:
        try:
            import httpx  # noqa: PLC0415
        except ImportError as exc:
            raise ImportError(
                "httpx is required for web search. "
                "Install it with: pip install httpx"
            ) from exc

        try:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.post(
                    "https://api.tavily.com/search",
                    json={
                        "api_key": self._tavily_key,
                        "query": query,
                        "max_results": top_k,
                        "search_depth": "basic",
                    },
                )
                response.raise_for_status()
                data = response.json()
        except Exception as exc:
            raise WebSearchError(f"Tavily API call failed: {exc}") from exc

        results: List[Dict] = []
        for item in data.get("results", [])[:top_k]:
            results.append(
                {
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "snippet": item.get("content", ""),
                }
            )
        logger.info("Tavily returned %d results for query %r.", len(results), query)
        return results


__all__ = ["WebSearchTool", "WebSearchError"]
