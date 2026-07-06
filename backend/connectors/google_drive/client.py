"""
connectors/google_drive/client.py

Thin wrapper around Google Drive REST API v3.

Responsibilities:
  - Authenticate requests with an access token
  - List files and folders (paginated)
  - Download files (handles Google Workspace native formats via export)
  - Get file metadata
  - Changes API for incremental sync
  - Webhook registration/cancellation

This module has NO database access and NO pipeline logic.
"""

from __future__ import annotations

import io
import logging
from datetime import datetime, timezone
from typing import Optional

import httpx

from connectors.models import (
    ChangeList,
    FileChange,
    FileChangeType,
    FileListResult,
    FileMetadata,
    WatchResponse,
)

logger = logging.getLogger(__name__)

DRIVE_API = "https://www.googleapis.com/drive/v3"
DRIVE_UPLOAD_API = "https://www.googleapis.com/upload/drive/v3"

# Google Workspace MIME types and their export targets
GOOGLE_WORKSPACE_EXPORT_MAP = {
    "application/vnd.google-apps.document": (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".docx",
    ),
    "application/vnd.google-apps.spreadsheet": (
        "text/csv",
        ".csv",
    ),
    "application/vnd.google-apps.presentation": (
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        ".pptx",
    ),
}

# MIME types that can be downloaded directly (not Google Workspace native formats)
SUPPORTED_DOWNLOAD_MIMES = {
    "application/pdf",
    "text/plain",
    "text/csv",
    "text/markdown",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-powerpoint",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
}

# File fields to request from Drive API
FILE_FIELDS = (
    "id,name,mimeType,size,modifiedTime,createdTime,parents,webViewLink,trashed"
)


def _parse_file_metadata(item: dict) -> FileMetadata:
    """Parse a Drive API file resource into our FileMetadata dataclass."""
    modified_at = None
    if item.get("modifiedTime"):
        try:
            modified_at = datetime.fromisoformat(
                item["modifiedTime"].replace("Z", "+00:00")
            )
        except Exception:
            pass

    created_at = None
    if item.get("createdTime"):
        try:
            created_at = datetime.fromisoformat(
                item["createdTime"].replace("Z", "+00:00")
            )
        except Exception:
            pass

    return FileMetadata(
        file_id=item["id"],
        name=item.get("name", ""),
        mime_type=item.get("mimeType", ""),
        size_bytes=int(item.get("size", 0)),
        modified_at=modified_at,
        created_at=created_at,
        parent_id=item.get("parents", [None])[0],
        web_url=item.get("webViewLink"),
        extra={"trashed": item.get("trashed", False)},
    )


class GoogleDriveClient:
    """
    Async Google Drive API v3 client.

    All methods require a valid access_token. Token refresh is handled
    by the caller (connector_service.py) before invoking this client.
    """

    def __init__(self, timeout: float = 60.0) -> None:
        self._timeout = timeout

    def _headers(self, access_token: str) -> dict:
        return {"Authorization": f"Bearer {access_token}"}

    async def list_files(
        self,
        access_token: str,
        folder_id: Optional[str] = None,
        page_token: Optional[str] = None,
        page_size: int = 100,
    ) -> FileListResult:
        """
        List files in a folder (or all of Drive if folder_id is None).

        Excludes trashed files and Google Workspace shortcuts.
        Returns only files with supported MIME types.
        """
        # Build query
        query_parts = [
            "trashed = false",
            "mimeType != 'application/vnd.google-apps.folder'",
        ]
        if folder_id:
            query_parts.append(f"'{folder_id}' in parents")

        params: dict = {
            "q": " and ".join(query_parts),
            "fields": f"nextPageToken,files({FILE_FIELDS})",
            "pageSize": page_size,
            "orderBy": "modifiedTime desc",
        }
        if page_token:
            params["pageToken"] = page_token

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.get(
                f"{DRIVE_API}/files",
                headers=self._headers(access_token),
                params=params,
            )
            resp.raise_for_status()
            data = resp.json()

        files = []
        for item in data.get("files", []):
            mime = item.get("mimeType", "")
            # Include Google Workspace docs (exportable) and supported binaries
            if mime in GOOGLE_WORKSPACE_EXPORT_MAP or mime in SUPPORTED_DOWNLOAD_MIMES:
                files.append(_parse_file_metadata(item))

        next_token = data.get("nextPageToken")
        return FileListResult(
            files=files,
            next_page_token=next_token,
            has_more=bool(next_token),
        )

    async def download_file(
        self,
        access_token: str,
        file_id: str,
        mime_type: Optional[str] = None,
    ) -> tuple[bytes, str]:
        """
        Download a file and return (content_bytes, suggested_filename).

        For Google Workspace native files (Docs, Sheets, Slides), the file
        is exported to an equivalent binary format via the export API.
        For regular files, the content is downloaded directly.
        """
        headers = self._headers(access_token)

        # First get metadata to know the MIME type and name
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            meta_resp = await client.get(
                f"{DRIVE_API}/files/{file_id}",
                headers=headers,
                params={"fields": "id,name,mimeType"},
            )
            meta_resp.raise_for_status()
            meta = meta_resp.json()

        file_name = meta.get("name", file_id)
        file_mime = mime_type or meta.get("mimeType", "")

        if file_mime in GOOGLE_WORKSPACE_EXPORT_MAP:
            # Export Google Workspace document
            export_mime, ext = GOOGLE_WORKSPACE_EXPORT_MAP[file_mime]
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.get(
                    f"{DRIVE_API}/files/{file_id}/export",
                    headers=headers,
                    params={"mimeType": export_mime},
                    follow_redirects=True,
                )
                resp.raise_for_status()
                content = resp.content

            # Ensure filename has the right extension
            if not file_name.endswith(ext):
                file_name = file_name + ext
        else:
            # Download binary file directly
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.get(
                    f"{DRIVE_API}/files/{file_id}",
                    headers=headers,
                    params={"alt": "media"},
                    follow_redirects=True,
                )
                resp.raise_for_status()
                content = resp.content

        logger.debug("Downloaded file '%s' (%d bytes)", file_name, len(content))
        return content, file_name

    async def get_file_metadata(self, access_token: str, file_id: str) -> FileMetadata:
        """Get metadata for a single file."""
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.get(
                f"{DRIVE_API}/files/{file_id}",
                headers=self._headers(access_token),
                params={"fields": FILE_FIELDS},
            )
            resp.raise_for_status()
            data = resp.json()

        return _parse_file_metadata(data)

    async def get_start_page_token(self, access_token: str) -> str:
        """Get the starting page token for tracking changes."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                f"{DRIVE_API}/changes/startPageToken",
                headers=self._headers(access_token),
            )
            resp.raise_for_status()
            data = resp.json()

        return data["startPageToken"]

    async def list_changes(
        self,
        access_token: str,
        page_token: str,
        page_size: int = 100,
    ) -> ChangeList:
        """
        List changes since the given page token.

        Returns a ChangeList containing added/modified/deleted files
        and a new page token for the next call.
        """
        params = {
            "pageToken": page_token,
            "fields": (
                "nextPageToken,newStartPageToken,"
                "changes(changeType,removed,fileId,file("
                f"{FILE_FIELDS}))"
            ),
            "pageSize": page_size,
            "includeRemoved": True,
        }

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.get(
                f"{DRIVE_API}/changes",
                headers=self._headers(access_token),
                params=params,
            )
            resp.raise_for_status()
            data = resp.json()

        changes = []
        for change in data.get("changes", []):
            file_id = change.get("fileId")
            if not file_id:
                continue

            if change.get("removed") or (
                change.get("file", {}).get("trashed", False)
            ):
                changes.append(FileChange(
                    file_id=file_id,
                    change_type=FileChangeType.DELETED,
                ))
            else:
                file_data = change.get("file")
                if file_data:
                    meta = _parse_file_metadata(file_data)
                    mime = meta.mime_type
                    # Only track files we can ingest
                    if mime in GOOGLE_WORKSPACE_EXPORT_MAP or mime in SUPPORTED_DOWNLOAD_MIMES:
                        changes.append(FileChange(
                            file_id=file_id,
                            change_type=FileChangeType.MODIFIED,
                            file_metadata=meta,
                        ))

        # The new token to use for the NEXT call
        new_token = data.get("newStartPageToken") or data.get("nextPageToken") or page_token

        return ChangeList(
            changes=changes,
            new_change_token=new_token,
            has_more=bool(data.get("nextPageToken")),
        )

    async def create_watch(
        self,
        access_token: str,
        channel_id: str,
        webhook_url: str,
    ) -> WatchResponse:
        """Register a push notification channel for Drive changes."""
        payload = {
            "id": channel_id,
            "type": "web_hook",
            "address": webhook_url,
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{DRIVE_API}/changes/watch",
                headers=self._headers(access_token),
                json=payload,
                params={"pageToken": "1"},
            )
            resp.raise_for_status()
            data = resp.json()

        expiry = None
        if data.get("expiration"):
            expiry = datetime.fromtimestamp(
                int(data["expiration"]) / 1000, tz=timezone.utc
            )

        return WatchResponse(
            channel_id=data["id"],
            resource_id=data.get("resourceId", ""),
            expiry=expiry,
        )

    async def stop_watch(
        self,
        access_token: str,
        channel_id: str,
        resource_id: str,
    ) -> None:
        """Stop a push notification channel."""
        payload = {"id": channel_id, "resourceId": resource_id}
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{DRIVE_API}/channels/stop",
                headers=self._headers(access_token),
                json=payload,
            )
            if resp.status_code not in (200, 204, 404):
                logger.warning("stop_watch returned %s", resp.status_code)


__all__ = ["GoogleDriveClient"]
