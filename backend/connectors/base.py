"""
connectors/base.py

Abstract base class defining the universal connector interface.

Every provider connector (Google Drive, SharePoint, OneDrive, Confluence,
Slack, Notion, S3) must implement this interface. The ingestion pipeline
is completely decoupled from any provider-specific logic.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from connectors.models import (
    ChangeList,
    FileListResult,
    FileMetadata,
    WatchResponse,
)


class BaseConnector(ABC):
    """
    Abstract interface all connectors must implement.

    Design principles:
    - Each method has a single responsibility.
    - No database access here — DB is the responsibility of the service layer.
    - No pipeline logic here — pipeline is triggered by the orchestrator.
    - Stateless: credentials/config are passed in or already stored externally.
    """

    # ── Identity ────────────────────────────────────────────────────────────

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Unique provider identifier, e.g. 'google_drive'."""

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable provider name, e.g. 'Google Drive'."""

    # ── Auth ────────────────────────────────────────────────────────────────

    @abstractmethod
    async def get_auth_url(self, state: str) -> str:
        """
        Return the OAuth2 authorization URL to redirect the user to.
        The state parameter is passed through for CSRF protection.
        """

    @abstractmethod
    async def exchange_code(self, auth_code: str, redirect_uri: str) -> dict:
        """
        Exchange an authorization code for access + refresh tokens.
        Returns a dict with at minimum: access_token, refresh_token, expires_in.
        """

    @abstractmethod
    async def refresh_token(self, refresh_token: str) -> dict:
        """
        Use the refresh token to get a new access token.
        Returns updated token dict.
        """

    @abstractmethod
    async def revoke_token(self, token: str) -> None:
        """Revoke the given token (called on disconnect)."""

    # ── File Operations ─────────────────────────────────────────────────────

    @abstractmethod
    async def list_files(
        self,
        access_token: str,
        folder_id: Optional[str] = None,
        page_token: Optional[str] = None,
    ) -> FileListResult:
        """
        List files in the remote source.
        Returns a paginated FileListResult. Caller handles pagination.
        """

    @abstractmethod
    async def download_file(
        self,
        access_token: str,
        file_id: str,
    ) -> tuple[bytes, str]:
        """
        Download a file and return (content_bytes, suggested_filename).
        Implementations must handle provider-specific formats (e.g., Google Docs → PDF).
        """

    @abstractmethod
    async def get_metadata(
        self,
        access_token: str,
        file_id: str,
    ) -> FileMetadata:
        """Get metadata for a single file."""

    # ── Change Detection ────────────────────────────────────────────────────

    @abstractmethod
    async def get_initial_change_token(self, access_token: str) -> str:
        """
        Get the starting change token for incremental sync.
        Call once after full sync; store the returned token.
        """

    @abstractmethod
    async def get_changes(
        self,
        access_token: str,
        change_token: str,
    ) -> ChangeList:
        """
        Get changes since the last change token.
        Returns a ChangeList with new/modified/deleted files and a new token.
        """

    # ── Webhooks (optional) ─────────────────────────────────────────────────

    async def setup_watch(
        self,
        access_token: str,
        webhook_url: str,
        channel_id: str,
    ) -> Optional[WatchResponse]:
        """
        Register a push notification webhook (optional — not all providers support it).
        Default implementation returns None (polling-only mode).
        """
        return None

    async def stop_watch(
        self,
        access_token: str,
        channel_id: str,
        resource_id: str,
    ) -> None:
        """Stop a previously registered webhook watch."""
        pass

    # ── Capability flags ────────────────────────────────────────────────────

    @property
    def supports_webhooks(self) -> bool:
        """Override to True if the provider supports push notifications."""
        return False

    @property
    def supports_incremental_sync(self) -> bool:
        """Override to False if the provider doesn't have a changes API."""
        return True

    @classmethod
    def get_credentials_schema(cls) -> list[dict]:
        """
        Return the schema for credentials required by this connector.
        Example: [{"name": "api_key", "label": "API Key", "type": "password", "required": True}]
        """
        return []


__all__ = ["BaseConnector"]
