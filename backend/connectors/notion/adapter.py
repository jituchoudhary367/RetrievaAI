import logging
from typing import AsyncIterator, List, Dict, Any, Optional
import httpx

from connectors.base.connector import BaseConnector
from connectors.base.metadata import ConnectorFileMetadata
from connectors.base.sync import SyncCursor
from connectors.base.capabilities import CapabilitySet, Capability
from connectors.base.exceptions import ConnectorError, ConnectorRateLimitError, ConnectorAuthError

from .auth import get_auth_url, exchange_code, refresh_token
from .mapper import map_notion_page, blocks_to_markdown

logger = logging.getLogger(__name__)

NOTION_VERSION = "2022-06-28"


class NotionAdapter(BaseConnector):
    """
    Notion adapter for the Enterprise Connector Framework.
    """

    def __init__(self):
        self.base_url = "https://api.notion.com/v1"
        self._access_token: Optional[str] = None

    @property
    def provider_name(self) -> str:
        return "notion"

    def capabilities(self) -> CapabilitySet:
        return {
            Capability.OAUTH,
            Capability.INCREMENTAL_SYNC,
            Capability.METADATA_EXTRACTION,
            Capability.BINARY_FILE_SUPPORT,
        }

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json",
        }

    async def authenticate(self, credentials: Dict[str, Any]) -> None:
        self._access_token = credentials.get("access_token")
        if not self._access_token:
            raise ValueError("NotionAdapter requires an access_token")

    async def get_auth_url(self, state: str) -> str:
        return get_auth_url(state)

    async def exchange_code(self, auth_code: str, redirect_uri: str) -> Dict[str, Any]:
        data, expires_at = await exchange_code(auth_code)
        # Notion returns bot_id and workspace info in the token response
        data["provider_user_id"] = data.get("owner", {}).get("user", {}).get("id")
        data["provider_email"] = (
            data.get("owner", {}).get("user", {}).get("person", {}).get("email")
        )
        return data

    async def refresh_token(self, refresh_token_str: str) -> Dict[str, Any]:
        data, _ = await refresh_token(refresh_token_str)
        return data

    async def revoke_token(self, token: str) -> None:
        pass

    async def health_check(self) -> Dict[str, Any]:
        if not self._access_token:
            return {"status": "error", "message": "Not authenticated"}
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.base_url}/users/me",
                    headers=self._headers(),
                )
                resp.raise_for_status()
            return {"status": "ok"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def _search_all(self, client: httpx.AsyncClient, filter_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Use Notion Search API to list all pages/databases."""
        results = []
        cursor = None
        while True:
            payload: Dict[str, Any] = {"page_size": 100}
            if filter_type:
                payload["filter"] = {"property": "object", "value": filter_type}
            if cursor:
                payload["start_cursor"] = cursor

            resp = await client.post(
                f"{self.base_url}/search",
                headers=self._headers(),
                json=payload,
            )
            if resp.status_code == 429:
                raise ConnectorRateLimitError("Rate limited by Notion API", retry_after=60)
            if not resp.is_success:
                raise ConnectorError(f"Notion search failed: {resp.text}")

            data = resp.json()
            results.extend(data.get("results", []))

            if data.get("has_more") and data.get("next_cursor"):
                cursor = data["next_cursor"]
            else:
                break
        return results

    async def _fetch_blocks(self, client: httpx.AsyncClient, block_id: str, depth: int = 0) -> List[Dict[str, Any]]:
        """
        Recursively fetch a block's children, capped at MAX_DEPTH.
        Children are embedded into the block dict under 'children'.
        """
        from .mapper import MAX_DEPTH
        if depth > MAX_DEPTH:
            logger.warning("Block children fetch depth cap reached at block %s (depth %d)", block_id, depth)
            return []

        blocks = []
        cursor = None
        while True:
            url = f"{self.base_url}/blocks/{block_id}/children"
            params = {"page_size": 100}
            if cursor:
                params["start_cursor"] = cursor

            resp = await client.get(url, headers=self._headers(), params=params)
            if resp.status_code == 429:
                raise ConnectorRateLimitError("Rate limited by Notion API", retry_after=60)
            if not resp.is_success:
                logger.error("Failed to fetch blocks for %s: %s", block_id, resp.text)
                break

            data = resp.json()
            for block in data.get("results", []):
                if block.get("has_children"):
                    block["children"] = await self._fetch_blocks(client, block["id"], depth + 1)
                else:
                    block["children"] = []
                blocks.append(block)

            if data.get("has_more") and data.get("next_cursor"):
                cursor = data["next_cursor"]
            else:
                break
        return blocks

    async def full_sync(self) -> AsyncIterator[ConnectorFileMetadata]:
        if not self._access_token:
            raise ConnectorAuthError("Not authenticated")

        async with httpx.AsyncClient() as client:
            items = await self._search_all(client)
            for item in items:
                yield map_notion_page(item)

    async def incremental_sync(self, cursor: SyncCursor) -> AsyncIterator[ConnectorFileMetadata]:
        # Notion Search doesn't support time-based filtering natively in the same way;
        # fall back to full sync. In production we'd diff against last_edited_time.
        async for item in self.full_sync():
            yield item

    async def detect_deletes(self, cursor: SyncCursor) -> AsyncIterator[str]:
        for x in []:
            yield x

    async def download_file(self, file_id: str) -> bytes:
        """Fetch a Notion page's block tree and return rendered Markdown bytes."""
        if not self._access_token:
            raise ConnectorAuthError("Not authenticated")

        async with httpx.AsyncClient() as client:
            blocks = await self._fetch_blocks(client, file_id)

        markdown = blocks_to_markdown(blocks)
        return markdown.encode("utf-8")

    async def get_permissions(self, file_id: str) -> List[Dict[str, Any]]:
        return []
