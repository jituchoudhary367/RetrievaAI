"""
db/models/connector.py

Connector database tables for multi-provider connector framework.

Tables:
  Connector            — one row per connected source per user
  ConnectorCredential  — OAuth tokens (access + refresh) per connector
  ConnectorSyncState   — last sync timestamp, change token, webhook state
  ConnectorFile        — maps remote file_id → local Document row

Design principles:
  - Does NOT modify existing Document or IngestionJob tables.
  - Linked to existing Document via nullable FK on ConnectorFile.
  - All tables are scoped by user_id for multi-tenant isolation.
  - Tokens are stored encrypted in ConnectorCredential.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base, TimestampMixin, _new_uuid


class Connector(Base, TimestampMixin):
    """One row per connected external source per user."""
    __tablename__ = "connectors"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=_new_uuid
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    # e.g. 'google_drive', 'sharepoint', 'notion'
    provider: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    display_name: Mapped[Optional[str]] = mapped_column(String(255))

    # status: pending_auth | connected | disconnected | error | syncing
    status: Mapped[str] = mapped_column(
        String(30), default="pending_auth", nullable=False, index=True
    )
    # Optional folder/root to sync from (null = sync all accessible files)
    root_folder_id: Mapped[Optional[str]] = mapped_column(String(255))
    root_folder_name: Mapped[Optional[str]] = mapped_column(String(512))

    # Whether to run incremental sync automatically
    auto_sync: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # sync_interval_minutes: how often to trigger incremental sync
    sync_interval_minutes: Mapped[int] = mapped_column(Integer, default=30)

    error_message: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    credential: Mapped[Optional["ConnectorCredential"]] = relationship(
        back_populates="connector", cascade="all, delete-orphan", uselist=False
    )
    sync_state: Mapped[Optional["ConnectorSyncState"]] = relationship(
        back_populates="connector", cascade="all, delete-orphan", uselist=False
    )
    files: Mapped[list["ConnectorFile"]] = relationship(
        back_populates="connector", cascade="all, delete-orphan"
    )


class ConnectorCredential(Base):
    """
    Stores OAuth credentials for a connector.
    Refresh token is the long-lived credential; access token is short-lived.
    In production, tokens should be encrypted at rest.
    """
    __tablename__ = "connector_credentials"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=_new_uuid
    )
    connector_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("connectors.id", ondelete="CASCADE"),
        nullable=False, unique=True, index=True
    )
    # Stored tokens (ideally encrypted)
    access_token: Mapped[Optional[str]] = mapped_column(Text)
    refresh_token: Mapped[Optional[str]] = mapped_column(Text, nullable=False)
    token_type: Mapped[str] = mapped_column(String(50), default="Bearer")
    scopes: Mapped[Optional[str]] = mapped_column(Text)  # space-separated
    # ISO datetime string of when the access token expires
    expires_at: Mapped[Optional[str]] = mapped_column(String(50))

    # Provider-specific user info (populated at connect time)
    provider_user_id: Mapped[Optional[str]] = mapped_column(String(255))
    provider_email: Mapped[Optional[str]] = mapped_column(String(255))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    connector: Mapped["Connector"] = relationship(back_populates="credential")


class ConnectorSyncState(Base):
    """
    Tracks the sync state for a connector.
    One row per connector, updated after each sync.
    """
    __tablename__ = "connector_sync_states"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=_new_uuid
    )
    connector_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("connectors.id", ondelete="CASCADE"),
        nullable=False, unique=True, index=True
    )

    # sync_mode: 'full' | 'incremental'
    last_sync_mode: Mapped[Optional[str]] = mapped_column(String(20))
    last_sync_started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    last_sync_completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    last_sync_status: Mapped[Optional[str]] = mapped_column(String(20))  # success | failed | running
    last_sync_error: Mapped[Optional[str]] = mapped_column(Text)

    # Counters from last sync
    files_discovered: Mapped[int] = mapped_column(Integer, default=0)
    files_synced: Mapped[int] = mapped_column(Integer, default=0)
    files_failed: Mapped[int] = mapped_column(Integer, default=0)
    files_deleted: Mapped[int] = mapped_column(Integer, default=0)

    # Google Drive Change API token for incremental sync
    change_token: Mapped[Optional[str]] = mapped_column(Text)

    # Webhook state
    webhook_channel_id: Mapped[Optional[str]] = mapped_column(String(255))
    webhook_resource_id: Mapped[Optional[str]] = mapped_column(String(255))
    webhook_expiry: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    connector: Mapped["Connector"] = relationship(back_populates="sync_state")


class ConnectorFile(Base):
    """
    Maps a remote file (identified by file_id) to a local Document row.

    This is the bridge between the connector layer and the document catalog.
    One row per file tracked by a connector.
    """
    __tablename__ = "connector_files"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=_new_uuid
    )
    connector_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("connectors.id", ondelete="CASCADE"),
        nullable=False, index=True
    )

    # Remote file identifier (stable across renames)
    remote_file_id: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    remote_file_name: Mapped[Optional[str]] = mapped_column(String(1024))
    remote_mime_type: Mapped[Optional[str]] = mapped_column(String(255))
    remote_modified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    remote_url: Mapped[Optional[str]] = mapped_column(Text)

    # Link to the ingested document (null until indexing completes)
    document_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True, index=True
    )
    # Link to the ingestion job that processed this file
    ingestion_job_id: Mapped[Optional[str]] = mapped_column(
        String(36), nullable=True, index=True
    )

    # sync_status: pending | syncing | indexed | failed | deleted
    sync_status: Mapped[str] = mapped_column(
        String(20), default="pending", nullable=False, index=True
    )
    sync_error: Mapped[Optional[str]] = mapped_column(Text)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)

    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )

    connector: Mapped["Connector"] = relationship(back_populates="files")


__all__ = [
    "Connector",
    "ConnectorCredential",
    "ConnectorSyncState",
    "ConnectorFile",
]
