import logging
from typing import AsyncIterator, List, Dict, Any, Optional
import httpx

from connectors.base.connector import BaseConnector
from connectors.base.metadata import ConnectorFileMetadata
from connectors.base.sync import SyncCursor
from connectors.base.capabilities import CapabilitySet, Capability
from connectors.base.exceptions import ConnectorError, ConnectorRateLimitError, ConnectorAuthError

from .auth import get_auth_url, exchange_code, refresh_token
from .mapper import map_confluence_page, convert_confluence_to_markdown

logger = logging.getLogger(__name__)

class ConfluenceAdapter(BaseConnector):
    """
    Atlassian Confluence adapter for the Enterprise Connector Framework.
    """
    
    def __init__(self):
        self.base_url = "https://api.atlassian.com/ex/confluence"
        self._access_token: Optional[str] = None
        self._cloud_id: Optional[str] = None
        
    @property
    def provider_name(self) -> str:
        return "confluence"
        
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
            raise ValueError("ConfluenceAdapter requires an access_token")
            
        # Confluence APIs require a cloud_id to route requests
        self._cloud_id = credentials.get("cloud_id")
        if not self._cloud_id:
            # Try to discover accessible resources if cloud_id is missing
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(
                        "https://api.atlassian.com/oauth/token/accessible-resources",
                        headers={"Authorization": f"Bearer {self._access_token}"}
                    )
                    resp.raise_for_status()
                    resources = resp.json()
                    if resources:
                        self._cloud_id = resources[0].get("id")
            except Exception as e:
                logger.error(f"Failed to discover Atlassian cloud_id: {e}")

    async def get_auth_url(self, state: str) -> str:
        return get_auth_url(state)

    async def exchange_code(self, auth_code: str, redirect_uri: str) -> Dict[str, Any]:
        data, expires_at = await exchange_code(auth_code)
        
        # After token exchange, we must get the cloud_id from accessible-resources
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://api.atlassian.com/oauth/token/accessible-resources",
                headers={"Authorization": f"Bearer {data.get('access_token')}"}
            )
            resp.raise_for_status()
            resources = resp.json()
            if not resources:
                raise ConnectorAuthError("User has no accessible Confluence resources")
                
            cloud_id = resources[0].get("id")
            data["cloud_id"] = cloud_id
            
            # Optionally get user profile
            try:
                user_resp = await client.get(
                    f"https://api.atlassian.com/ex/confluence/{cloud_id}/rest/api/user/current",
                    headers={"Authorization": f"Bearer {data.get('access_token')}"}
                )
                user_data = user_resp.json()
                data["provider_user_id"] = user_data.get("accountId")
                data["provider_email"] = user_data.get("email")
            except Exception:
                pass
                
        return data

    async def refresh_token(self, refresh_token_str: str) -> Dict[str, Any]:
        data, expires_at = await refresh_token(refresh_token_str)
        # We should ideally re-fetch cloud_id but it's usually stable.
        return data

    async def revoke_token(self, token: str) -> None:
        pass

    async def health_check(self) -> Dict[str, Any]:
        if not self._access_token or not self._cloud_id:
            return {"status": "error", "message": "Not authenticated or missing cloud_id"}
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.base_url}/{self._cloud_id}/rest/api/space",
                    headers={"Authorization": f"Bearer {self._access_token}"}
                )
                resp.raise_for_status()
            return {"status": "ok"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def full_sync(self) -> AsyncIterator[ConnectorFileMetadata]:
        if not self._access_token or not self._cloud_id:
            raise ConnectorAuthError("Not authenticated")
            
        async with httpx.AsyncClient() as client:
            # 1. List spaces
            spaces_url = f"{self.base_url}/{self._cloud_id}/rest/api/space?limit=50"
            spaces = []
            
            while spaces_url:
                resp = await client.get(spaces_url, headers={"Authorization": f"Bearer {self._access_token}"})
                if resp.status_code == 429:
                    raise ConnectorRateLimitError(f"Rate limited by Confluence API", retry_after=60)
                if not resp.is_success:
                    raise ConnectorError(f"Failed to list spaces: {resp.text}")
                    
                data = resp.json()
                for space in data.get("results", []):
                    spaces.append(space.get("key"))
                    
                _links = data.get("_links", {})
                if "next" in _links:
                    spaces_url = f"{self.base_url}/{self._cloud_id}{_links['next']}"
                else:
                    spaces_url = None
                    
            # 2. List pages for each space
            for space_key in spaces:
                pages_url = f"{self.base_url}/{self._cloud_id}/rest/api/content?spaceKey={space_key}&type=page&expand=body.storage,version&limit=50"
                
                while pages_url:
                    resp = await client.get(pages_url, headers={"Authorization": f"Bearer {self._access_token}"})
                    if resp.status_code == 429:
                        raise ConnectorRateLimitError(f"Rate limited by Confluence API", retry_after=60)
                    if not resp.is_success:
                        logger.error(f"Failed to list pages in space {space_key}: {resp.text}")
                        break
                        
                    data = resp.json()
                    for page in data.get("results", []):
                        yield map_confluence_page(page, space_key)
                        
                    _links = data.get("_links", {})
                    if "next" in _links:
                        pages_url = f"{self.base_url}/{self._cloud_id}{_links['next']}"
                    else:
                        pages_url = None

    async def incremental_sync(self, cursor: SyncCursor) -> AsyncIterator[ConnectorFileMetadata]:
        # For simplicity, fallback to full sync in this mock implementation
        async for item in self.full_sync():
            yield item

    async def detect_deletes(self, cursor: SyncCursor) -> AsyncIterator[str]:
        for x in []:
            yield x

    async def download_file(self, file_id: str) -> bytes:
        if not self._access_token or not self._cloud_id:
            raise ConnectorAuthError("Not authenticated")
            
        async with httpx.AsyncClient(follow_redirects=True) as client:
            resp = await client.get(
                f"{self.base_url}/{self._cloud_id}/rest/api/content/{file_id}?expand=body.storage",
                headers={"Authorization": f"Bearer {self._access_token}"}
            )
            if not resp.is_success:
                raise ConnectorError(f"Failed to get confluence page {file_id}: {resp.text}")
                
            page = resp.json()
            body_storage = page.get("body", {}).get("storage", {}).get("value", "")
            
            # Critical constraint: Convert storage format to markdown before returning
            markdown_content = convert_confluence_to_markdown(body_storage)
            
            return markdown_content.encode('utf-8')

    async def get_permissions(self, file_id: str) -> List[Dict[str, Any]]:
        return []
