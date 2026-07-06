"""
connectors/google_drive/connector.py

Google Drive implementation of BaseConnector.

Delegates all API calls to GoogleDriveClient and all auth
operations to the google_drive.auth module.
"""

from __future__ import annotations

import logging
from typing import Optional

from connectors.base import BaseConnector
from connectors.google_drive.auth import (
    build_auth_url,
    exchange_code,
    refresh_access_token,
    revoke_token,
)
from connectors.google_drive.client import GoogleDriveClient
from connectors.models import (
    ChangeList,
    FileListResult,
    FileMetadata,
    WatchResponse,
)
from app.config import get_settings

logger = logging.getLogger(__name__)


class GoogleDriveConnector(BaseConnector):
    """
    Google Drive connector — implements BaseConnector using the Drive API v3.

    Supports:
    - OAuth2 authentication with refresh
    - Full file listing (paginated)
    - Incremental sync via Changes API
    - Webhook push notifications (optional)
    - Download of native files and exported Google Workspace formats
    """

    def __init__(self) -> None:
        self._client = GoogleDriveClient()

    @property
    def provider_name(self) -> str:
        return "google_drive"

    @property
    def display_name(self) -> str:
        return "Google Drive"

    @property
    def supports_webhooks(self) -> bool:
        cfg = get_settings()
        return bool(cfg.connectors.google_drive_webhook_url)

    @property
    def supports_incremental_sync(self) -> bool:
        return True

    # ── Auth ────────────────────────────────────────────────────────────────

    async def get_auth_url(self, state: str) -> str:
        cfg = get_settings()
        return build_auth_url(
            state=state,
            redirect_uri=cfg.connectors.google_drive_redirect_uri,
        )

    async def exchange_code(self, auth_code: str, redirect_uri: str) -> dict:
        return await exchange_code(auth_code, redirect_uri)

    async def refresh_token(self, refresh_token: str) -> dict:
        return await refresh_access_token(refresh_token)

    async def revoke_token(self, token: str) -> None:
        await revoke_token(token)

    # ── File Operations ─────────────────────────────────────────────────────

    async def list_files(
        self,
        access_token: str,
        folder_id: Optional[str] = None,
        page_token: Optional[str] = None,
    ) -> FileListResult:
        return await self._client.list_files(
            access_token=access_token,
            folder_id=folder_id,
            page_token=page_token,
        )

    async def download_file(
        self,
        access_token: str,
        file_id: str,
    ) -> tuple[bytes, str]:
        return await self._client.download_file(
            access_token=access_token,
            file_id=file_id,
        )

    async def get_metadata(
        self,
        access_token: str,
        file_id: str,
    ) -> FileMetadata:
        return await self._client.get_file_metadata(
            access_token=access_token,
            file_id=file_id,
        )

    # ── Change Detection ────────────────────────────────────────────────────

    async def get_initial_change_token(self, access_token: str) -> str:
        return await self._client.get_start_page_token(access_token)

    async def get_changes(
        self,
        access_token: str,
        change_token: str,
    ) -> ChangeList:
        return await self._client.list_changes(
            access_token=access_token,
            page_token=change_token,
        )

    # ── Webhooks ────────────────────────────────────────────────────────────

    async def setup_watch(
        self,
        access_token: str,
        webhook_url: str,
        channel_id: str,
    ) -> Optional[WatchResponse]:
        try:
            return await self._client.create_watch(
                access_token=access_token,
                channel_id=channel_id,
                webhook_url=webhook_url,
            )
        except Exception as exc:
            logger.warning("Failed to set up Drive webhook: %s", exc)
            return None

    async def stop_watch(
        self,
        access_token: str,
        channel_id: str,
        resource_id: str,
    ) -> None:
        await self._client.stop_watch(
            access_token=access_token,
            channel_id=channel_id,
            resource_id=resource_id,
        )


__all__ = ["GoogleDriveConnector"]
