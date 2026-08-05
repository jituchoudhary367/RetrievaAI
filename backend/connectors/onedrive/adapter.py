import logging
from typing import AsyncIterator, List, Dict, Any, Optional
import httpx
from datetime import datetime, timezone

from connectors.base.connector import BaseConnector
from connectors.base.metadata import ConnectorFileMetadata
from connectors.base.sync import SyncCursor
from connectors.base.capabilities import CapabilitySet, Capability
from connectors.base.exceptions import ConnectorError, ConnectorRateLimitError, ConnectorAuthError

from .auth import get_auth_url, exchange_code, refresh_token
from .mapper import map_onedrive_item

logger = logging.getLogger(__name__)

class OneDriveAdapter(BaseConnector):
    """
    Microsoft OneDrive adapter for the Enterprise Connector Framework.
    """
    
    def __init__(self):
        self.base_url = "https://graph.microsoft.com/v1.0"
        self._access_token: Optional[str] = None
        
    @property
    def provider_name(self) -> str:
        return "onedrive"
        
    def capabilities(self) -> CapabilitySet:
        return {
            Capability.OAUTH,
            Capability.INCREMENTAL_SYNC,
            Capability.METADATA_EXTRACTION,
            Capability.BINARY_FILE_SUPPORT
        }
        
    async def authenticate(self, credentials: Dict[str, Any]) -> None:
        self._access_token = credentials.get("access_token")
        if not self._access_token:
            raise ValueError("OneDriveAdapter requires an access_token")

    async def get_auth_url(self, state: str) -> str:
        return get_auth_url(state)

    async def exchange_code(self, auth_code: str, redirect_uri: str) -> Dict[str, Any]:
        # Exchange code
        data, expires_at = await exchange_code(auth_code)
        
        # Get user info
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/me",
                headers={"Authorization": f"Bearer {data.get('access_token')}"}
            )
            resp.raise_for_status()
            user_data = resp.json()
            
        data["provider_user_id"] = user_data.get("id")
        data["provider_email"] = user_data.get("userPrincipalName")
        return data

    async def refresh_token(self, refresh_token_str: str) -> Dict[str, Any]:
        data, expires_at = await refresh_token(refresh_token_str)
        return data

    async def revoke_token(self, token: str) -> None:
        # Microsoft doesn't have a simple revoke endpoint for delegated tokens in the same way,
        # but we can just drop it locally.
        pass

    async def health_check(self) -> Dict[str, Any]:
        if not self._access_token:
            return {"status": "error", "message": "Not authenticated"}
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.base_url}/me/drive",
                    headers={"Authorization": f"Bearer {self._access_token}"}
                )
                resp.raise_for_status()
            return {"status": "ok"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # pyrefly: ignore [bad-override]
    async def full_sync(self) -> AsyncIterator[ConnectorFileMetadata]:
        if not self._access_token:
            raise ConnectorAuthError("Not authenticated")
            
        url = f"{self.base_url}/me/drive/root/delta"
        
        async with httpx.AsyncClient() as client:
            while url:
                resp = await client.get(url, headers={"Authorization": f"Bearer {self._access_token}"})
                if resp.status_code == 429:
                    retry_after = int(resp.headers.get("Retry-After", 60))
                    # pyrefly: ignore [unexpected-keyword]
                    raise ConnectorRateLimitError(f"Rate limited by Graph API", retry_after=retry_after)
                if resp.status_code == 401:
                    raise ConnectorAuthError("Invalid access token")
                if not resp.is_success:
                    raise ConnectorError(f"Failed to list files: {resp.text}")
                    
                data = resp.json()
                
                for item in data.get("value", []):
                    if "deleted" in item:
                        continue
                    yield map_onedrive_item(item)
                    
                url = data.get("@odata.nextLink")

    async def incremental_sync(self, cursor: SyncCursor) -> AsyncIterator[ConnectorFileMetadata]:
        # For simplicity, fallback to full sync in this mock implementation
        async for item in self.full_sync():
            yield item

    async def detect_deletes(self, cursor: SyncCursor) -> AsyncIterator[str]:
        # Mock empty list
        for x in []:
            yield x

    async def download_file(self, file_id: str) -> bytes:
        if not self._access_token:
            raise ConnectorAuthError("Not authenticated")
        
        async with httpx.AsyncClient(follow_redirects=True) as client:
            meta_resp = await client.get(
                f"{self.base_url}/me/drive/items/{file_id}",
                headers={"Authorization": f"Bearer {self._access_token}"}
            )
            if not meta_resp.is_success:
                raise ConnectorError(f"Failed to get file metadata: {meta_resp.text}")
                
            item = meta_resp.json()
            download_url = item.get("@microsoft.graph.downloadUrl")
            
            if not download_url:
                raise ConnectorError(f"No download URL available for {file_id}. Is it a folder?")
                
            dl_resp = await client.get(download_url)
            if not dl_resp.is_success:
                raise ConnectorError(f"Failed to download file {file_id}")
                
            return dl_resp.content

    async def get_permissions(self, file_id: str) -> List[Dict[str, Any]]:
        return []
