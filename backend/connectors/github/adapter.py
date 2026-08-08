import logging
import asyncio
import base64
import time
from typing import AsyncIterator, List, Dict, Any, Optional
import httpx

from connectors.base.connector import BaseConnector
from connectors.base.metadata import ConnectorFileMetadata
from connectors.base.sync import SyncCursor
from connectors.base.capabilities import CapabilitySet, Capability
from connectors.base.exceptions import ConnectorError, ConnectorRateLimitError, ConnectorAuthError

from .auth import get_auth_url, exchange_code, refresh_token
from .mapper import map_github_file, map_github_release, is_indexable_file

logger = logging.getLogger(__name__)


class GithubAdapter(BaseConnector):
    """
    GitHub adapter for the Enterprise Connector Framework.
    """

    def __init__(self):
        self.base_url = "https://api.github.com"
        self._access_token: Optional[str] = None
        # Cache release markdown content
        self._release_cache: Dict[str, str] = {}

    @property
    def provider_name(self) -> str:
        return "github"

    def capabilities(self) -> CapabilitySet:
        return {
            Capability.OAUTH,
            Capability.INCREMENTAL_SYNC,
            Capability.METADATA_EXTRACTION,
            # In the future, Capability.ISSUES or Capability.TICKETS could be added here
        }

    @classmethod
    def get_credentials_schema(cls) -> list[dict]:
        return [
            {"name": "access_token", "label": "GitHub Personal Access Token (PAT)", "type": "password", "required": True},
        ]

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    async def authenticate(self, credentials: Dict[str, Any]) -> None:
        self._access_token = credentials.get("access_token")
        if not self._access_token:
            raise ValueError("GithubAdapter requires an access_token")

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
            resp = await self._api_call("user")
            if resp.get("login"):
                return {"status": "ok"}
            return {"status": "error", "message": "Unknown user"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def _api_call(self, endpoint: str, params: Dict[str, Any] = None) -> Any:
        """Make a GitHub API call with explicit rate limit handling."""
        url = f"{self.base_url}/{endpoint}" if not endpoint.startswith("http") else endpoint
        max_retries = 3
        
        async with httpx.AsyncClient() as client:
            for attempt in range(max_retries):
                resp = await client.get(url, headers=self._headers(), params=params)

                # GitHub returns 403 or 429 for rate limits
                if resp.status_code in (403, 429):
                    # Check X-RateLimit-Remaining
                    remaining = resp.headers.get("X-RateLimit-Remaining")
                    if remaining == "0":
                        reset_time = int(resp.headers.get("X-RateLimit-Reset", 0))
                        now = int(time.time())
                        retry_after = max(1, reset_time - now)
                        
                        # Hard cap the sleep so we don't hang the worker for an hour
                        if retry_after > 300: # 5 minutes max wait
                            raise ConnectorRateLimitError(f"GitHub rate limit exceeded, resets in {retry_after}s")
                            
                        logger.warning(f"GitHub rate limit hit. Sleeping for {retry_after}s...")
                        await asyncio.sleep(retry_after)
                        continue
                    
                    # Secondary rate limits (abuse detection) return 403 with a Retry-After header
                    retry_after_hdr = resp.headers.get("Retry-After")
                    if retry_after_hdr:
                        retry_after = int(retry_after_hdr)
                        logger.warning(f"GitHub secondary rate limit hit. Sleeping for {retry_after}s...")
                        await asyncio.sleep(retry_after)
                        continue

                resp.raise_for_status()
                return resp.json()

        raise ConnectorRateLimitError("Max retries exceeded for GitHub rate limits")

    async def _paginate(self, endpoint: str, params: Dict[str, Any] = None) -> AsyncIterator[Any]:
        """Helper to paginate through GitHub list endpoints."""
        if params is None:
            params = {}
        params["per_page"] = 100
        page = 1
        
        while True:
            params["page"] = page
            data = await self._api_call(endpoint, params=params)
            
            if not data:
                break
                
            for item in data:
                yield item
                
            if len(data) < 100:
                break
                
            page += 1

    async def full_sync(self) -> AsyncIterator[ConnectorFileMetadata]:
        if not self._access_token:
            raise ConnectorAuthError("Not authenticated")

        # 1. Discover Repositories (User's repos)
        async for repo in self._paginate("user/repos"):
            repo_full_name = repo.get("full_name")
            default_branch = repo.get("default_branch", "main")
            
            # 2. Fetch the Git Tree (recursive)
            try:
                tree_data = await self._api_call(f"repos/{repo_full_name}/git/trees/{default_branch}?recursive=1")
                tree = tree_data.get("tree", [])
                
                for item in tree:
                    if item.get("type") == "blob":
                        path = item.get("path", "")
                        if is_indexable_file(path):
                            yield map_github_file(item, repo_full_name)
                            
            except httpx.HTTPStatusError as e:
                # E.g. 404 if repo is completely empty
                if e.response.status_code == 404:
                    logger.warning(f"Repo {repo_full_name} returned 404 for tree fetch (likely empty)")
                elif e.response.status_code == 409: # Git Repository is empty
                    logger.warning(f"Repo {repo_full_name} is empty")
                else:
                    raise e
                    
            # 3. Fetch Releases
            try:
                async for release in self._paginate(f"repos/{repo_full_name}/releases"):
                    doc = map_github_release(release, repo_full_name)
                    self._release_cache[doc.external_id] = doc.raw_metadata.pop("markdown_content", "")
                    yield doc
            except httpx.HTTPStatusError as e:
                if e.response.status_code not in (404, 409):
                    raise e

    async def incremental_sync(self, cursor: SyncCursor) -> AsyncIterator[ConnectorFileMetadata]:
        # Fallback to full sync in this mock implementation
        async for item in self.full_sync():
            yield item

    async def detect_deletes(self, cursor: SyncCursor) -> AsyncIterator[str]:
        for x in []:
            yield x

    async def download_file(self, file_id: str) -> bytes:
        if not self._access_token:
            raise ConnectorAuthError("Not authenticated")

        # Check if it's a cached release document
        if file_id in self._release_cache:
            return self._release_cache[file_id].encode("utf-8")

        # Otherwise it's a file blob: "repo:{repo}:blob:{sha}"
        if file_id.startswith("repo:") and ":blob:" in file_id:
            parts = file_id.split(":")
            repo_full_name = parts[1]
            # Since repo_full_name could contain a colon (unlikely but possible), it's safer to partition
            _, _, rest = file_id.partition(":blob:")
            sha = rest
            
            repo_name = file_id[5:file_id.find(":blob:")]

            # Fetch blob content via Git Database API
            data = await self._api_call(f"repos/{repo_name}/git/blobs/{sha}")
            content = data.get("content", "")
            encoding = data.get("encoding", "")
            
            if encoding == "base64":
                try:
                    return base64.b64decode(content)
                except Exception as e:
                    raise ConnectorError(f"Failed to decode base64 blob {sha}: {e}")
            elif encoding == "utf-8":
                return content.encode("utf-8")
            else:
                return content.encode("utf-8")

        raise ConnectorError(f"Unknown file id type: {file_id}")

    async def get_permissions(self, file_id: str) -> List[Dict[str, Any]]:
        return []
