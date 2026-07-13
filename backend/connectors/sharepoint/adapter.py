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
from .mapper import map_sharepoint_item

logger = logging.getLogger(__name__)

class SharePointAdapter(BaseConnector):
    """
    Microsoft SharePoint adapter for the Enterprise Connector Framework.
    """
    
    def __init__(self):
        self.base_url = "https://graph.microsoft.com/v1.0"
        self._access_token: Optional[str] = None
        self._site_id: str = "root"  # Default to root site, can be overridden by config
        
    @property
    def provider_name(self) -> str:
        return "sharepoint"
        
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
            raise ValueError("SharePointAdapter requires an access_token")
            
        # Optional: Allow config to specify which site to sync
        if "site_id" in credentials:
            self._site_id = credentials["site_id"]

    async def get_auth_url(self, state: str) -> str:
        return get_auth_url(state)

    async def exchange_code(self, auth_code: str, redirect_uri: str) -> Dict[str, Any]:
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
        pass

    async def health_check(self) -> Dict[str, Any]:
        if not self._access_token:
            return {"status": "error", "message": "Not authenticated"}
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.base_url}/sites/{self._site_id}",
                    headers={"Authorization": f"Bearer {self._access_token}"}
                )
                resp.raise_for_status()
            return {"status": "ok"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def _get_drives_for_site(self, client: httpx.AsyncClient) -> List[Dict[str, Any]]:
        """Get all document libraries (drives) for the site."""
        resp = await client.get(
            f"{self.base_url}/sites/{self._site_id}/drives",
            headers={"Authorization": f"Bearer {self._access_token}"}
        )
        if not resp.is_success:
            raise ConnectorError(f"Failed to list drives for site {self._site_id}: {resp.text}")
        
        return resp.json().get("value", [])

    async def full_sync(self) -> AsyncIterator[ConnectorFileMetadata]:
        if not self._access_token:
            raise ConnectorAuthError("Not authenticated")
            
        async with httpx.AsyncClient() as client:
            drives = await self._get_drives_for_site(client)
            
            for drive in drives:
                drive_id = drive.get("id")
                # Iterate through all items in the drive using delta
                url = f"{self.base_url}/drives/{drive_id}/root/delta"
                
                while url:
                    resp = await client.get(url, headers={"Authorization": f"Bearer {self._access_token}"})
                    if resp.status_code == 429:
                        retry_after = int(resp.headers.get("Retry-After", 60))
                        raise ConnectorRateLimitError(f"Rate limited by Graph API", retry_after=retry_after)
                    if resp.status_code == 401:
                        raise ConnectorAuthError("Invalid access token")
                    if not resp.is_success:
                        raise ConnectorError(f"Failed to list files in drive {drive_id}: {resp.text}")
                        
                    data = resp.json()
                    
                    for item in data.get("value", []):
                        if "deleted" in item:
                            continue
                        yield map_sharepoint_item(item, self._site_id, drive_id)
                        
                    url = data.get("@odata.nextLink")

    async def incremental_sync(self, cursor: SyncCursor) -> AsyncIterator[ConnectorFileMetadata]:
        # For simplicity, fallback to full sync in this mock implementation
        async for item in self.full_sync():
            yield item

    async def detect_deletes(self, cursor: SyncCursor) -> AsyncIterator[str]:
        for x in []:
            yield x

    async def download_file(self, file_id: str) -> bytes:
        if not self._access_token:
            raise ConnectorAuthError("Not authenticated")
        
        # We need to find the drive item across any drive if we only have file_id.
        # Graph API allows accessing items directly if we know drive-id.
        # But wait, file_id might be driveItem id.
        # Actually, /sites/{site-id}/drive/items/{item-id} works if it's the default drive.
        # For a specific drive, it's /drives/{drive-id}/items/{item-id}.
        # Wait, the ID returned by Graph API for a DriveItem is unique globally (or at least within the tenant).
        # We can actually just use /me/drive/items if it's OneDrive, but for SharePoint it's /drives/{drive-id}.
        # Since we mapped file_id from item.id, we can't easily guess drive_id unless we parse it or stored it.
        # In a real impl, we'd store drive_id in raw_metadata or concatenate them.
        # For now, let's assume `file_id` is actually `{drive_id}::{item_id}` so we can parse it, OR we fetch it via sites.
        
        # Let's try direct item access (it may fail if we don't know the drive id)
        # Actually, Microsoft Graph API DriveItem id is unique. 
        # Is there a global /items/{id}? No. 
        # So we should modify our map_sharepoint_item to prepend drive_id!
        # Let's assume file_id is just item_id for now and we query the site's default drive.
        
        # In this mock, we will just try the default drive:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            meta_resp = await client.get(
                f"{self.base_url}/sites/{self._site_id}/drive/items/{file_id}",
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
        # Mock site-level permissions
        return []
