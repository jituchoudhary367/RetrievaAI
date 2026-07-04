"""
db/models/telemetry.py

Telemetry ORM models — written fire-and-forget after every query/search (§1.1).

QueryEvent       — one row per /api/query call.
QueryEventCitation — child table; one row per citation returned.
SearchEvent      — one row per /api/search call.
SearchClickEvent — one row when the user clicks a search result card.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger, Boolean, DateTime, Float, ForeignKey,
    Integer, String, Text, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base, _new_uuid


class QueryEvent(Base):
    __tablename__ = "query_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    session_id: Mapped[Optional[str]] = mapped_column(String(36), index=True)
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    intent: Mapped[Optional[str]] = mapped_column(String(50))
    used_cache: Mapped[bool] = mapped_column(Boolean, default=False)
    used_web_search: Mapped[bool] = mapped_column(Boolean, default=False)
    used_code_search: Mapped[bool] = mapped_column(Boolean, default=False)
    crag_corrections: Mapped[int] = mapped_column(Integer, default=0)
    retrieval_latency_ms: Mapped[Optional[float]] = mapped_column(Float)
    generation_latency_ms: Mapped[Optional[float]] = mapped_column(Float)
    total_latency_ms: Mapped[Optional[float]] = mapped_column(Float)
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    embedding_calls: Mapped[int] = mapped_column(Integer, default=0)
    rerank_calls: Mapped[int] = mapped_column(Integer, default=0)
    retrieved_count: Mapped[int] = mapped_column(Integer, default=0)
    reranked_count: Mapped[int] = mapped_column(Integer, default=0)
    top_k: Mapped[int] = mapped_column(Integer, default=5)
    model_name: Mapped[Optional[str]] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    citations: Mapped[list["QueryEventCitation"]] = relationship(
        back_populates="event", cascade="all, delete-orphan"
    )


class QueryEventCitation(Base):
    """One row per citation returned in a QueryEvent response."""
    __tablename__ = "query_event_citations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    query_event_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("query_events.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    document_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    source: Mapped[Optional[str]] = mapped_column(Text)
    score: Mapped[Optional[float]] = mapped_column(Float)

    event: Mapped["QueryEvent"] = relationship(back_populates="citations")


class SearchEvent(Base):
    __tablename__ = "search_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    result_count: Mapped[int] = mapped_column(Integer, default=0)
    latency_ms: Mapped[Optional[float]] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    clicks: Mapped[list["SearchClickEvent"]] = relationship(
        back_populates="search_event", cascade="all, delete-orphan"
    )


class SearchClickEvent(Base):
    """Written when a user clicks a result card (POST /api/search/events/click)."""
    __tablename__ = "search_click_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    search_event_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("search_events.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    chunk_id: Mapped[str] = mapped_column(String(36), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    search_event: Mapped["SearchEvent"] = relationship(back_populates="clicks")
