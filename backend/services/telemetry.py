"""
services/telemetry.py

Fire-and-forget telemetry recording (§1.1).

Every /api/query and /api/search call writes one row after responding —
telemetry is a side effect, never blocking the response.

Functions:
  record_query_event(...)    — writes QueryEvent + QueryEventCitation rows
  record_search_event(...)   — writes SearchEvent row
  record_search_click(...)   — writes SearchClickEvent row

All functions are async and wrapped in asyncio.create_task() by callers
so they never block the HTTP response.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from db.engine import async_session_factory
from db.models.telemetry import (
    QueryEvent,
    QueryEventCitation,
    SearchClickEvent,
    SearchEvent,
)

logger = logging.getLogger(__name__)


async def record_query_event(
    *,
    tenant_id: str,
    user_id: Optional[str],
    session_id: Optional[str],
    query_text: str,
    intent: Optional[str] = None,
    used_cache: bool = False,
    used_web_search: bool = False,
    used_code_search: bool = False,
    crag_corrections: int = 0,
    retrieval_latency_ms: Optional[float] = None,
    generation_latency_ms: Optional[float] = None,
    total_latency_ms: Optional[float] = None,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    total_tokens: int = 0,
    retrieved_count: int = 0,
    reranked_count: int = 0,
    top_k: int = 5,
    model_name: Optional[str] = None,
    citations: Optional[List[dict]] = None,
) -> None:
    """Write a QueryEvent row (and citation child rows) to Postgres."""
    try:
        async with async_session_factory() as db:
            event = QueryEvent(
                tenant_id=tenant_id,
                user_id=user_id,
                session_id=session_id,
                query_text=query_text,
                intent=intent,
                used_cache=used_cache,
                used_web_search=used_web_search,
                used_code_search=used_code_search,
                crag_corrections=crag_corrections,
                retrieval_latency_ms=retrieval_latency_ms,
                generation_latency_ms=generation_latency_ms,
                total_latency_ms=total_latency_ms,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                retrieved_count=retrieved_count,
                reranked_count=reranked_count,
                top_k=top_k,
                model_name=model_name,
            )
            db.add(event)
            await db.flush()  # get the event.id

            for cit in (citations or []):
                db.add(QueryEventCitation(
                    query_event_id=event.id,
                    document_id=cit.get("document_id", ""),
                    source=cit.get("source"),
                    score=cit.get("score"),
                ))

            await db.commit()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Telemetry: failed to write QueryEvent: %s", exc)


async def record_search_event(
    *,
    tenant_id: str,
    user_id: Optional[str],
    query_text: str,
    result_count: int,
    latency_ms: Optional[float] = None,
) -> str:
    """Write a SearchEvent row and return its ID (needed for click events)."""
    event_id = ""
    try:
        async with async_session_factory() as db:
            event = SearchEvent(
                tenant_id=tenant_id,
                user_id=user_id,
                query_text=query_text,
                result_count=result_count,
                latency_ms=latency_ms,
            )
            db.add(event)
            await db.flush()
            event_id = event.id
            await db.commit()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Telemetry: failed to write SearchEvent: %s", exc)
    return event_id


async def record_search_click(
    *,
    search_event_id: str,
    chunk_id: str,
) -> None:
    """Write a SearchClickEvent — called by POST /api/search/events/click."""
    try:
        async with async_session_factory() as db:
            db.add(SearchClickEvent(
                search_event_id=search_event_id,
                chunk_id=chunk_id,
            ))
            await db.commit()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Telemetry: failed to write SearchClickEvent: %s", exc)


__all__ = ["record_query_event", "record_search_event", "record_search_click"]
