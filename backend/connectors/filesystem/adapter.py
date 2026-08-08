import logging
import os
from typing import AsyncIterator, Dict, Any, List, Optional

from connectors.base.connector import BaseConnector
from connectors.base.metadata import ConnectorFileMetadata
from connectors.base.sync import SyncCursor
from connectors.base.capabilities import CapabilitySet, Capability
from connectors.base.exceptions import ConnectorError, ConnectorAuthError

from .mapper import map_filesystem_file, map_filesystem_event, is_indexable, compute_checksum

logger = logging.getLogger(__name__)

class FilesystemAdapter(BaseConnector):
    """
    Filesystem connector for on-premise/self-hosted deployments.
    Authentication: local path configuration (no external auth).
    Full Sync: Iterates all files in the configured root directory.
    Incremental Sync: Event-driven via a file-system watcher (e.g. watchdog).
      - The caller/orchestrator is responsible for running the watchdog observer
        and passing events to `process_watchdog_event()`.
    """

    def __init__(self):
        self._root_dir: Optional[str] = None
        # In-memory cache to help download_file locate files by checksum
        self._checksum_cache: Dict[str, str] = {}

    @property
    def provider_name(self) -> str:
        return "filesystem"

    def capabilities(self) -> CapabilitySet:
        return {
            Capability.INCREMENTAL_SYNC,
            Capability.CHANGE_NOTIFICATIONS,
            Capability.METADATA_EXTRACTION,
            Capability.BINARY_FILE_SUPPORT,
            Capability.DELETE_EVENTS,
        }

    @classmethod
    def get_credentials_schema(cls) -> list[dict]:
        return [
            {"name": "root_dir", "label": "Absolute Root Directory Path", "type": "text", "required": True},
        ]

    async def authenticate(self, credentials: Dict[str, Any]) -> None:
        self._root_dir = credentials.get("root_dir")
        if not self._root_dir:
            raise ConnectorAuthError("FilesystemAdapter requires 'root_dir' in credentials")
        if not os.path.isdir(self._root_dir):
            raise ConnectorAuthError(f"Root directory does not exist or is not a directory: {self._root_dir}")

    async def get_auth_url(self, state: str) -> str:
        raise ConnectorError("Filesystem uses local path config, not OAuth")

    async def exchange_code(self, auth_code: str, redirect_uri: str) -> Dict[str, Any]:
        raise ConnectorError("Filesystem uses local path config, not OAuth")

    async def refresh_token(self, refresh_token_str: str) -> Dict[str, Any]:
        return {}

    async def revoke_token(self, token: str) -> None:
        pass

    async def health_check(self) -> Dict[str, Any]:
        if not self._root_dir:
            return {"status": "error", "message": "Not configured"}
        if os.path.isdir(self._root_dir):
            return {"status": "ok"}
        return {"status": "error", "message": "Root directory unavailable"}

    async def full_sync(self) -> AsyncIterator[ConnectorFileMetadata]:
        if not self._root_dir:
            raise ConnectorAuthError("Not configured")

        for root, _, files in os.walk(self._root_dir):
            for file in files:
                file_path = os.path.join(root, file)
                if is_indexable(file_path):
                    metadata = map_filesystem_file(file_path, self._root_dir)
                    if metadata.external_id.startswith("fs://"):
                        checksum = metadata.external_id[5:]
                        self._checksum_cache[checksum] = file_path
                    yield metadata

    async def incremental_sync(self, cursor: SyncCursor) -> AsyncIterator[ConnectorFileMetadata]:
        # Incremental sync is event-driven via watchdog
        async for item in self.full_sync():
            yield item

    async def detect_deletes(self, cursor: SyncCursor) -> AsyncIterator[str]:
        for x in []:
            yield x

    def process_watchdog_event(self, event_type: str, src_path: str, dest_path: str = "") -> Optional[ConnectorFileMetadata]:
        """
        Process a filesystem event (from watchdog or similar).
        event_type: 'created', 'modified', 'deleted', 'moved'
        """
        if not self._root_dir:
            return None

        # For delete events, since we use checksum as ID, we'd need to know the checksum of the deleted file.
        # But the file is gone. If the orchestrator relies on ID, we can't reliably yield a delete by checksum
        # unless we had it cached. If not in cache, we yield path and orchestrator might not find it if it only keys by checksum.
        # However, the assignment specifically asks to return None for deletes and let the caller handle tombstoning.
        
        parsed = map_filesystem_event(event_type, src_path, dest_path)
        action = parsed["action"]
        
        if action == "delete":
            return None  # Caller handles tombstoning

        path_to_index = dest_path if event_type == "moved" else src_path
        
        if not os.path.exists(path_to_index) or not is_indexable(path_to_index):
            return None

        metadata = map_filesystem_file(path_to_index, self._root_dir)
        if metadata.external_id.startswith("fs://"):
            checksum = metadata.external_id[5:]
            self._checksum_cache[checksum] = path_to_index
            
        return metadata

    async def download_file(self, file_id: str) -> bytes:
        """
        Download file content. file_id is fs://<checksum> or fs-path://<relative_path>
        """
        if not self._root_dir:
            raise ConnectorAuthError("Not configured")

        if file_id.startswith("fs-path://"):
            rel_path = file_id[10:]
            target_path = os.path.join(self._root_dir, rel_path)
        elif file_id.startswith("fs://"):
            checksum = file_id[5:]
            target_path = self._checksum_cache.get(checksum)
            
            # If not in cache (e.g. distributed worker), scan for it
            if not target_path or not os.path.exists(target_path) or compute_checksum(target_path) != checksum:
                target_path = None
                for root, _, files in os.walk(self._root_dir):
                    for file in files:
                        p = os.path.join(root, file)
                        if compute_checksum(p) == checksum:
                            target_path = p
                            self._checksum_cache[checksum] = target_path
                            break
                    if target_path:
                        break
                        
            if not target_path:
                raise ConnectorError(f"File with checksum {checksum} not found in root directory")
        else:
            raise ConnectorError(f"Invalid filesystem file_id: {file_id}")

        try:
            with open(target_path, "rb") as f:
                return f.read()
        except OSError as e:
            raise ConnectorError(f"Failed to read file: {e}")

    async def get_permissions(self, file_id: str) -> List[Dict[str, Any]]:
        return []
