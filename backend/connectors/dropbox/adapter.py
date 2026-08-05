import logging
import asyncio
from typing import AsyncIterator, List, Dict, Any, Optional
import httpx

from connectors.base.connector import BaseConnector
from connectors.base.metadata import ConnectorFileMetadata
from connectors.base.sync import SyncCursor
from connectors.base.capabilities import CapabilitySet, Capability
from connectors.base.exceptions import ConnectorError, ConnectorRateLimitError, ConnectorAuthError

from .auth import get_auth_url, exchange_code, refresh_token, revoke_token
from .mapper import map_dropbox_file, map_dropbox_deleted, is_indexable

logger = logging.getLogger(__name__)

FILES_API = "https://api.dropboxapi.com/2/files"
CONTENT_API = "https://content.dropboxapi.com/2/files"
WEBHOOK_API = "https://api.dropboxapi.com/2/files/list_folder/continue"


class DropboxAdapter(BaseConnector):
    """
    Dropbox adapter for the Enterprise Connector Framework.
    Supports full sync via list_folder + incremental sync via list_folder/continue (longpoll).
    Webhook registration is handled separately via register_webhook().
    """

    def __init__(self):
        self._access_token: Optional[str] = None
        self._refresh_token: Optional[str] = None

    @property
    def provider_name(self) -> str:
        return "dropbox"

    def capabilities(self) -> CapabilitySet:
        return {
            Capability.OAUTH,
            Capability.INCREMENTAL_SYNC,
            Capability.WEBHOOKS,
            Capability.METADATA_EXTRACTION,
            Capability.BINARY_FILE_SUPPORT,
        }

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }

    async def authenticate(self, credentials: Dict[str, Any]) -> None:
        self._access_token = credentials.get("access_token")
        self._refresh_token = credentials.get("refresh_token")
        if not self._access_token:
            raise ValueError("DropboxAdapter requires an access_token")

    async def get_auth_url(self, state: str) -> str:
        return get_auth_url(state)

    async def exchange_code(self, auth_code: str, redirect_uri: str) -> Dict[str, Any]:
        data, expires_at = await exchange_code(auth_code)
        return data

    async def refresh_token(self, refresh_token_str: str) -> Dict[str, Any]:
        data, _ = await refresh_token(refresh_token_str)
        self._access_token = data["access_token"]
        return data

    async def revoke_token(self, token: str) -> None:
        await revoke_token(token)

    async def health_check(self) -> Dict[str, Any]:
        if not self._access_token:
            return {"status": "error", "message": "Not authenticated"}
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "https://api.dropboxapi.com/2/users/get_current_account",
                    headers=self._headers(),
                    content=b"null",
                )
                resp.raise_for_status()
                data = resp.json()
                return {"status": "ok", "account_id": data.get("account_id")}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def _post(self, url: str, body: Dict[str, Any], *, retries: int = 3) -> Dict[str, Any]:
        """POST to a Dropbox API endpoint with rate-limit backoff."""
        async with httpx.AsyncClient() as client:
            for attempt in range(retries):
                resp = await client.post(url, headers=self._headers(), json=body)

                if resp.status_code == 429:
                    retry_after = int(resp.headers.get("Retry-After", 60))
                    logger.warning(f"Dropbox rate limit hit (429). Sleeping {retry_after}s…")
                    await asyncio.sleep(retry_after)
                    continue

                resp.raise_for_status()
                return resp.json()

        raise ConnectorRateLimitError("Max retries exceeded for Dropbox rate limits")

    async def full_sync(self) -> AsyncIterator[ConnectorFileMetadata]:
        if not self._access_token:
            raise ConnectorAuthError("Not authenticated")

        # Start listing from root, recursively
        data = await self._post(
            f"{FILES_API}/list_folder",
            {"path": "", "recursive": True, "include_deleted": False, "limit": 2000},
        )

        while True:
            for entry in data.get("entries", []):
                if entry.get(".tag") == "file":
                    path = entry.get("path_lower", "")
                    if is_indexable(path):
                        yield map_dropbox_file(entry)

            has_more = data.get("has_more", False)
            cursor = data.get("cursor")
            if not has_more or not cursor:
                break

            # Continue pagination
            data = await self._post(f"{FILES_API}/list_folder/continue", {"cursor": cursor})

    async def incremental_sync(self, cursor: SyncCursor) -> AsyncIterator[ConnectorFileMetadata]:
        """
        Use the stored Dropbox cursor to fetch only changes since last sync.
        The cursor is persisted in the SyncCursor object by the orchestrator.
        """
        if not self._access_token:
            raise ConnectorAuthError("Not authenticated")

        dropbox_cursor = cursor.provider_cursor if cursor else None

        if not dropbox_cursor:
            # No cursor — fall back to full sync
            async for item in self.full_sync():
                yield item
            return

        data = await self._post(
            f"{FILES_API}/list_folder/continue",
            {"cursor": dropbox_cursor},
        )

        while True:
            for entry in data.get("entries", []):
                if entry.get(".tag") == "file":
                    path = entry.get("path_lower", "")
                    if is_indexable(path):
                        yield map_dropbox_file(entry)
                # Deletions are surfaced via detect_deletes

            has_more = data.get("has_more", False)
            new_cursor = data.get("cursor")
            if not has_more or not new_cursor:
                # Update the cursor on the SyncCursor object so the orchestrator persists it
                if new_cursor and cursor:
                    cursor.provider_cursor = new_cursor
                break

            data = await self._post(
                f"{FILES_API}/list_folder/continue",
                {"cursor": new_cursor},
            )

    async def detect_deletes(self, cursor: SyncCursor) -> AsyncIterator[str]:
        """
        Yield path_lower strings of deleted files from the last delta.
        The orchestrator maps them to internal IDs and tombstones the records.
        """
        if not self._access_token or not cursor or not cursor.provider_cursor:
            return

        data = await self._post(
            f"{FILES_API}/list_folder/continue",
            {"cursor": cursor.provider_cursor},
        )

        for entry in data.get("entries", []):
            if entry.get(".tag") == "deleted":
                yield map_dropbox_deleted(entry)

    async def download_file(self, file_id: str) -> bytes:
        """Download file content from Dropbox using the file ID."""
        if not self._access_token:
            raise ConnectorAuthError("Not authenticated")

        import json
        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Dropbox-API-Arg": json.dumps({"path": file_id}),
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{CONTENT_API}/download",
                headers=headers,
            )

            if resp.status_code == 429:
                raise ConnectorRateLimitError("Rate limited while downloading from Dropbox")

            resp.raise_for_status()
            return resp.content

    async def get_permissions(self, file_id: str) -> List[Dict[str, Any]]:
        return []

    async def register_webhook(self, callback_url: str) -> Dict[str, Any]:
        """
        Register a Dropbox webhook endpoint. Dropbox uses a simple verify-then-notify model.
        The actual registration is done via the Dropbox Developer console per-app,
        but we can programmatically confirm the endpoint is live.

        Note: Dropbox does not currently expose a REST API to dynamically add webhook URIs
        (they are set per-app in the developer console). This method records the intent
        and can be used for future dynamic registration if Dropbox exposes it.
        """
        logger.info(f"Dropbox webhook endpoint configured: {callback_url}")
        return {
            "status": "registered",
            "callback_url": callback_url,
            "note": "Webhook URI must also be set in the Dropbox developer console for your app."
        }
