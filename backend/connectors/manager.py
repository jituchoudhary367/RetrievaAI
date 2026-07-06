"""
connectors/manager.py

High-level connector lifecycle management.

This is the thin coordination layer between API routes and the
connector service. It doesn't implement business logic itself;
it delegates to connector_service.py for DB operations and to
individual connector instances for API calls.
"""

from __future__ import annotations

import logging
from typing import Optional

from connectors.registry import ConnectorRegistry
from connectors.models import ConnectorStatusEnum

logger = logging.getLogger(__name__)


class ConnectorManager:
    """
    Manages the lifecycle of a single connector instance.

    Usage:
        manager = ConnectorManager("google_drive")
        auth_url = await manager.get_auth_url(state="xyz")
        tokens = await manager.exchange_code(code, redirect_uri)
    """

    def __init__(self, provider_name: str) -> None:
        self._provider_name = provider_name
        self._connector = ConnectorRegistry.create(provider_name)

    @property
    def provider_name(self) -> str:
        return self._provider_name

    @property
    def display_name(self) -> str:
        return self._connector.display_name

    @property
    def supports_webhooks(self) -> bool:
        return self._connector.supports_webhooks

    @property
    def supports_incremental_sync(self) -> bool:
        return self._connector.supports_incremental_sync

    async def get_auth_url(self, state: str) -> str:
        """Get the OAuth authorization URL to redirect the user to."""
        return await self._connector.get_auth_url(state=state)

    async def exchange_code(self, auth_code: str, redirect_uri: str) -> dict:
        """Exchange authorization code for tokens."""
        return await self._connector.exchange_code(auth_code, redirect_uri)

    async def refresh_token(self, refresh_token: str) -> dict:
        """Refresh an expired access token."""
        return await self._connector.refresh_token(refresh_token)

    async def revoke_token(self, token: str) -> None:
        """Revoke access on disconnect."""
        await self._connector.revoke_token(token)

    async def list_files(self, access_token: str, folder_id: Optional[str] = None, page_token: Optional[str] = None):
        """List files from the remote source."""
        return await self._connector.list_files(access_token, folder_id, page_token)

    async def download_file(self, access_token: str, file_id: str) -> tuple[bytes, str]:
        """Download a file, returning (bytes, filename)."""
        return await self._connector.download_file(access_token, file_id)

    async def get_metadata(self, access_token: str, file_id: str):
        """Get metadata for a single file."""
        return await self._connector.get_metadata(access_token, file_id)

    async def get_initial_change_token(self, access_token: str) -> str:
        """Get change token after initial full sync."""
        return await self._connector.get_initial_change_token(access_token)

    async def get_changes(self, access_token: str, change_token: str):
        """Get incremental changes since last sync."""
        return await self._connector.get_changes(access_token, change_token)

    async def setup_watch(self, access_token: str, webhook_url: str, channel_id: str):
        """Register webhook if the provider supports it."""
        return await self._connector.setup_watch(access_token, webhook_url, channel_id)

    async def stop_watch(self, access_token: str, channel_id: str, resource_id: str) -> None:
        """Stop a webhook watch."""
        await self._connector.stop_watch(access_token, channel_id, resource_id)


__all__ = ["ConnectorManager"]
