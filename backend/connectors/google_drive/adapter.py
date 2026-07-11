import logging
from typing import AsyncIterator, List, Dict, Any, Optional

from connectors.base.connector import BaseConnector
from connectors.base.metadata import ConnectorFileMetadata, ConnectorPermission
from connectors.base.sync import SyncCursor
from connectors.base.capabilities import CapabilitySet, Capability

from .client import GoogleDriveClient
from .mapper import map_drive_file_to_metadata

logger = logging.getLogger(__name__)

ADAPTER_VERSION = "1.0.0"

class GoogleDriveConnector(BaseConnector):
    """
    Reference implementation of the new BaseConnector contract for Google Drive.
    """
    def __init__(self):
        self._client = GoogleDriveClient()
        self._access_token: Optional[str] = None
        self._refresh_token: Optional[str] = None

    @property
    def provider_name(self) -> str:
        return "google_drive"

    def capabilities(self) -> CapabilitySet:
        return {
            Capability.OAUTH,
            Capability.INCREMENTAL_SYNC,
            Capability.WEBHOOKS,
            Capability.METADATA_EXTRACTION,
            Capability.BINARY_FILE_SUPPORT,
            Capability.CHANGE_NOTIFICATIONS
        }

    async def authenticate(self, credentials: Dict[str, Any]) -> None:
        self._access_token = credentials.get("access_token")
        self._refresh_token = credentials.get("refresh_token")
        if not self._access_token:
            raise ValueError("GoogleDriveConnector requires an access_token in credentials.")

    async def refresh_token(self) -> None:
        from .auth import refresh_access_token
        if not self._refresh_token:
            raise ValueError("No refresh_token available.")
        
        token_data = await refresh_access_token(self._refresh_token)
        self._access_token = token_data["access_token"]
        if "refresh_token" in token_data:
            self._refresh_token = token_data["refresh_token"]

    async def health_check(self) -> Dict[str, Any]:
        if not self._access_token:
            return {"status": "error", "message": "Not authenticated"}
        try:
            # Simple check to see if we can list files (limit 1)
            await self._client.list_files(self._access_token, page_size=1)
            return {"status": "ok"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def full_sync(self) -> AsyncIterator[ConnectorFileMetadata]:
        page_token = None
        while True:
            # In client.py, list_files returns FileListResult which has `files` as FileMetadata
            # Wait, the existing list_files parses them into FileMetadata using `_parse_file_metadata`. 
            # We want to yield `ConnectorFileMetadata`.
            # For simplicity, we can fetch from client and map them. Since `_parse_file_metadata` loses raw data,
            # we should ideally have client.py return raw, or we map `FileMetadata` to `ConnectorFileMetadata`.
            # Let's map from what `client.list_files` currently returns to avoid changing client.py yet.
            result = await self._client.list_files(
                access_token=self._access_token,
                page_token=page_token,
                page_size=100
            )
            for f in result.files:
                yield ConnectorFileMetadata(
                    external_id=f.file_id,
                    name=f.name,
                    mime_type=f.mime_type,
                    size_bytes=f.size_bytes,
                    external_path=f.parent_id,
                )
            
            page_token = result.next_page_token
            if not result.has_more or not page_token:
                break

    async def incremental_sync(self, cursor: SyncCursor) -> AsyncIterator[ConnectorFileMetadata]:
        # Implementation via client.get_changes
        page_token = cursor.token
        while True:
            result = await self._client.get_changes(
                access_token=self._access_token,
                page_token=page_token
            )
            for change in result.changes:
                if change.file_metadata:
                    yield ConnectorFileMetadata(
                        external_id=change.file_metadata.file_id,
                        name=change.file_metadata.name,
                        mime_type=change.file_metadata.mime_type,
                        size_bytes=change.file_metadata.size_bytes,
                        external_path=change.file_metadata.parent_id,
                    )
            
            page_token = result.new_change_token
            if not result.has_more or not page_token:
                break

    async def download_file(self, external_id: str) -> bytes:
        content_bytes, _ = await self._client.download_file(
            access_token=self._access_token,
            file_id=external_id
        )
        return content_bytes

    async def detect_deletes(self, known_ids: List[str]) -> List[str]:
        # Not natively supported by batch in drive without changes API, but we could check individually
        return []

    async def get_permissions(self, external_id: str) -> List[ConnectorPermission]:
        return []

    async def register_webhook(self, callback_url: str) -> Optional[Dict[str, Any]]:
        # Call client.watch_changes
        return None
