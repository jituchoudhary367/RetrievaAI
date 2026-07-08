"""
db/models/workspace_settings.py

Three new tables for the Enterprise AI Control Center.
All tables are scoped by user_id (each user = workspace owner).
Schema designed so a Workspace entity can be introduced later
without major refactoring — just add workspace_id FK.

Tables:
  workspace_providers       — LLM / Embedding / Search provider configs
  workspace_models          — Cached model catalog per provider
  workspace_runtime_config  — Workspace-level pipeline tuning (KV)
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean, DateTime, Float, Integer, String, Text,
    UniqueConstraint, func,
)
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base, _new_uuid


# ──────────────────────────────────────────────────────────────────────────────
# workspace_providers
# ──────────────────────────────────────────────────────────────────────────────

class WorkspaceProvider(Base):
    """
    Stores workspace-scoped provider configurations.

    provider_type:   'llm' | 'embedding' | 'search'
    provider_name:   'groq' | 'openai' | 'anthropic' | 'gemini' |
                     'openrouter' | 'deepseek' | 'azure_openai' | 'ollama' |
                     'cohere' | 'voyage' | 'jina' | 'mixedbread' |
                     'serper' | 'tavily' | 'brave' | 'exa' | 'duckduckgo'
    config_json:     AES-encrypted JSON blob containing api_key, model,
                     endpoint, temperature, etc.
    status:          'connected' | 'disconnected' | 'error' | 'validating'
    """
    __tablename__ = "workspace_providers"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "provider_type", "provider_name",
            name="uq_workspace_provider_user_type_name",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    # Future: add workspace_id FK here
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    provider_type: Mapped[str] = mapped_column(String(20), nullable=False)   # llm/embedding/search
    provider_name: Mapped[str] = mapped_column(String(50), nullable=False)   # groq/openai/...
    display_name: Mapped[Optional[str]] = mapped_column(String(100))

    # Encrypted config blob (AES-256-GCM)
    config_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")

    # Selection state
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_fallback: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Health
    status: Mapped[str] = mapped_column(String(20), default="disconnected", nullable=False)
    health_status: Mapped[Optional[str]] = mapped_column(String(20))          # healthy/degraded/down
    last_validated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[Optional[str]] = mapped_column(Text)
    latency_ms: Mapped[Optional[float]] = mapped_column(Float)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


# ──────────────────────────────────────────────────────────────────────────────
# workspace_models
# ──────────────────────────────────────────────────────────────────────────────

class WorkspaceModel(Base):
    """
    Cached model catalog fetched from each provider's API.
    Also stores per-model user preferences (favorite, default).
    """
    __tablename__ = "workspace_models"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "provider_name", "model_id",
            name="uq_workspace_model_user_provider_model",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    provider_name: Mapped[str] = mapped_column(String(50), nullable=False)
    model_id: Mapped[str] = mapped_column(String(200), nullable=False)        # API model identifier
    model_name: Mapped[str] = mapped_column(String(200), nullable=False)      # Human-readable

    # Capabilities
    context_window: Mapped[Optional[int]] = mapped_column(Integer)
    input_cost_per_1m: Mapped[Optional[float]] = mapped_column(Float)         # USD per 1M tokens
    output_cost_per_1m: Mapped[Optional[float]] = mapped_column(Float)
    supports_streaming: Mapped[bool] = mapped_column(Boolean, default=True)
    supports_vision: Mapped[bool] = mapped_column(Boolean, default=False)
    supports_json_mode: Mapped[bool] = mapped_column(Boolean, default=False)
    supports_function_calling: Mapped[bool] = mapped_column(Boolean, default=False)
    supports_reasoning: Mapped[bool] = mapped_column(Boolean, default=False)
    is_recommended: Mapped[bool] = mapped_column(Boolean, default=False)

    # User preferences
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False)

    last_fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


# ──────────────────────────────────────────────────────────────────────────────
# workspace_runtime_config
# ──────────────────────────────────────────────────────────────────────────────

class WorkspaceRuntimeConfig(Base):
    """
    Workspace-level pipeline tuning stored as a simple KV table.
    Falls back to global get_settings() defaults for any key not set here.

    Keys include: chunk_size, chunk_overlap, top_k, rerank_top_n,
    hybrid_alpha, cache_ttl, memory_window, streaming_enabled,
    crag_enabled, web_search_enabled, ocr_enabled, vision_enabled,
    telemetry_enabled, analytics_enabled, etc.
    """
    __tablename__ = "workspace_runtime_config"
    __table_args__ = (
        UniqueConstraint("user_id", "key", name="uq_workspace_runtime_user_key"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    key: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False, comment="JSON value")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


__all__ = ["WorkspaceProvider", "WorkspaceModel", "WorkspaceRuntimeConfig"]
