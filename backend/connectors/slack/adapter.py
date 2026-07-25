import logging
import asyncio
from typing import AsyncIterator, List, Dict, Any, Optional
import httpx

from connectors.base.connector import BaseConnector
from connectors.base.metadata import ConnectorFileMetadata
from connectors.base.sync import SyncCursor
from connectors.base.capabilities import CapabilitySet, Capability
from connectors.base.exceptions import ConnectorError, ConnectorRateLimitError, ConnectorAuthError

from .auth import get_auth_url, exchange_code, refresh_token
from .mapper import map_slack_thread, map_slack_attachment

logger = logging.getLogger(__name__)


class SlackAdapter(BaseConnector):
    """
    Slack adapter for the Enterprise Connector Framework.
    """

    def __init__(self):
        self.base_url = "https://slack.com/api"
        self._access_token: Optional[str] = None
        # In-memory cache to support download_file for threads
        self._thread_markdown_cache: Dict[str, str] = {}

    @property
    def provider_name(self) -> str:
        return "slack"

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
            "Content-Type": "application/x-www-form-urlencoded",
        }

    async def authenticate(self, credentials: Dict[str, Any]) -> None:
        self._access_token = credentials.get("access_token")
        if not self._access_token:
            raise ValueError("SlackAdapter requires an access_token")

    async def get_auth_url(self, state: str) -> str:
        return get_auth_url(state)

    async def exchange_code(self, auth_code: str, redirect_uri: str) -> Dict[str, Any]:
        data, expires_at = await exchange_code(auth_code)
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
            resp = await self._api_call("auth.test", method="POST")
            if resp.get("ok"):
                return {"status": "ok"}
            return {"status": "error", "message": resp.get("error")}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def _api_call(self, endpoint: str, method: str = "GET", params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make a Slack API call with explicit rate limit handling."""
        url = f"{self.base_url}/{endpoint}"
        max_retries = 3
        
        async with httpx.AsyncClient() as client:
            for attempt in range(max_retries):
                if method == "GET":
                    resp = await client.get(url, headers=self._headers(), params=params)
                else:
                    resp = await client.post(url, headers=self._headers(), data=params)

                if resp.status_code == 429:
                    retry_after = int(resp.headers.get("Retry-After", 60))
                    logger.warning(f"Slack rate limit hit (429). Sleeping for {retry_after}s...")
                    await asyncio.sleep(retry_after)
                    continue

                resp.raise_for_status()
                data = resp.json()
                if not data.get("ok"):
                    logger.error(f"Slack API error on {endpoint}: {data.get('error')}")
                
                return data

        raise ConnectorRateLimitError(f"Max retries exceeded for Slack rate limits (waited 60s max)")

    async def full_sync(self) -> AsyncIterator[ConnectorFileMetadata]:
        if not self._access_token:
            raise ConnectorAuthError("Not authenticated")

        # 1. Discover Channels
        channels_resp = await self._api_call("conversations.list", params={"types": "public_channel", "limit": 100})
        channels = channels_resp.get("channels", [])

        # 2. Sync Threads in each Channel
        for channel in channels:
            channel_id = channel.get("id")
            
            # Get top-level messages
            history_resp = await self._api_call("conversations.history", params={"channel": channel_id, "limit": 100})
            messages = history_resp.get("messages", [])

            for msg in messages:
                thread_ts = msg.get("thread_ts", msg.get("ts"))
                
                # Fetch full thread replies
                replies_resp = await self._api_call("conversations.replies", params={"channel": channel_id, "ts": thread_ts, "limit": 100})
                thread_msgs = replies_resp.get("messages", [msg])

                # Map thread to a document
                doc = map_slack_thread(thread_ts, channel_id, thread_msgs)
                
                # Cache the markdown so we can serve it when the orchestrator calls download_file
                self._thread_markdown_cache[thread_ts] = doc.raw_metadata.pop("markdown_content", "")
                
                yield doc

                # Yield attachments as separate files
                for thread_msg in thread_msgs:
                    for file_obj in thread_msg.get("files", []):
                        if file_obj.get("mode") != "tombstone": # skip deleted files
                            yield map_slack_attachment(file_obj, channel_id, thread_ts)


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

        # Check if it's a thread document
        if file_id in self._thread_markdown_cache:
            return self._thread_markdown_cache[file_id].encode("utf-8")

        # Otherwise it's a file attachment id (prefixed with 'file_')
        if file_id.startswith("file_"):
            real_id = file_id[5:]
            
            # Fetch file info to get the private URL
            file_info = await self._api_call("files.info", params={"file": real_id})
            url_private = file_info.get("file", {}).get("url_private")
            
            if not url_private:
                raise ConnectorError(f"Could not get download URL for Slack file {real_id}")
            
            # Download the actual file bytes using the private URL with the token
            async with httpx.AsyncClient(follow_redirects=True) as client:
                headers = {"Authorization": f"Bearer {self._access_token}"}
                resp = await client.get(url_private, headers=headers)
                resp.raise_for_status()
                return resp.content

        raise ConnectorError(f"Unknown file id type: {file_id}")

    async def get_permissions(self, file_id: str) -> List[Dict[str, Any]]:
        return []
