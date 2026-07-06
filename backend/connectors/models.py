"""
connectors/models.py

Shared dataclasses for the connector framework.
Every connector implementation uses these common result types.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional


class ConnectorStatusEnum(str, Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    SYNCING = "syncing"
    ERROR = "error"
    PENDING_AUTH = "pending_auth"


class SyncMode(str, Enum):
    FULL = "full"
    INCREMENTAL = "incremental"


class FileChangeType(str, Enum):
    ADDED = "added"
    MODIFIED = "modified"
    DELETED = "deleted"


@dataclass
class FileMetadata:
    """Metadata for a single remote file."""
    file_id: str
    name: str
    mime_type: str
    size_bytes: int = 0
    modified_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    parent_id: Optional[str] = None
    web_url: Optional[str] = None
    # Provider-specific extra fields
    extra: Dict = field(default_factory=dict)


@dataclass
class FileListResult:
    """Result of listing files from a connector."""
    files: List[FileMetadata] = field(default_factory=list)
    next_page_token: Optional[str] = None
    has_more: bool = False


@dataclass
class FileChange:
    """Represents a single file change event."""
    file_id: str
    change_type: FileChangeType
    file_metadata: Optional[FileMetadata] = None  # None for deletions


@dataclass
class ChangeList:
    """Result of a changes API call."""
    changes: List[FileChange] = field(default_factory=list)
    new_change_token: Optional[str] = None
    has_more: bool = False


@dataclass
class WatchResponse:
    """Result of registering a webhook watch."""
    channel_id: str
    resource_id: str
    expiry: Optional[datetime] = None


@dataclass
class ConnectorStatus:
    """Status summary for a connector."""
    connector_id: str
    provider: str
    status: ConnectorStatusEnum
    last_sync_at: Optional[datetime] = None
    files_synced: int = 0
    files_failed: int = 0
    error_message: Optional[str] = None


__all__ = [
    "ConnectorStatusEnum",
    "SyncMode",
    "FileChangeType",
    "FileMetadata",
    "FileListResult",
    "FileChange",
    "ChangeList",
    "WatchResponse",
    "ConnectorStatus",
]
