"""
Azure Blob Storage Connector Adapter
-------------------------------------
Authentication: Azure Storage connection string or SAS token.
Full Sync: Iterates all blobs in configured containers via list_blobs().
Incremental Sync: Event-driven via Azure Event Grid events (BlobCreated/BlobDeleted).
  - process_event_grid_event() handles individual events dispatched by the orchestrator.
"""

import logging
import os
from typing import AsyncIterator, Dict, Any, List, Optional

from connectors.base.connector import BaseConnector
from connectors.base.metadata import ConnectorFileMetadata
from connectors.base.sync import SyncCursor
from connectors.base.capabilities import CapabilitySet, Capability
from connectors.base.exceptions import ConnectorError, ConnectorAuthError

from .mapper import map_azure_blob, map_azure_event_grid, is_indexable

logger = logging.getLogger(__name__)

try:
    from azure.storage.blob import BlobServiceClient
    from azure.core.exceptions import AzureError
    AZURE_SDK_AVAILABLE = True
except ImportError:
    AZURE_SDK_AVAILABLE = False
    BlobServiceClient = None  # type: ignore


class AzureBlobAdapter(BaseConnector):
    """
    Azure Blob Storage connector.
    Uses a connection string or SAS token (not OAuth).
    """

    def __init__(self):
        self._connection_string: Optional[str] = None
        self._sas_token: Optional[str] = None
        self._account_name: Optional[str] = None
        self._containers: List[str] = []
        self._client = None

    @property
    def provider_name(self) -> str:
        return "azure_blob"

    def capabilities(self) -> CapabilitySet:
        return {
            Capability.API_KEY_AUTH,
            Capability.INCREMENTAL_SYNC,
            Capability.CHANGE_NOTIFICATIONS,
            Capability.METADATA_EXTRACTION,
            Capability.BINARY_FILE_SUPPORT,
            Capability.DELETE_EVENTS,
        }

    @classmethod
    def get_credentials_schema(cls) -> list[dict]:
        return [
            {"name": "connection_string", "label": "Azure Storage Connection String", "type": "password", "required": True},
        ]

    async def authenticate(self, credentials: Dict[str, Any]) -> None:
        self._connection_string = credentials.get("connection_string")
        self._sas_token = credentials.get("sas_token")
        self._account_name = credentials.get("account_name")
        self._containers = credentials.get("containers", [])

        if not self._connection_string and not self._sas_token:
            raise ConnectorAuthError(
                "AzureBlobAdapter requires either connection_string or sas_token"
            )

        if AZURE_SDK_AVAILABLE:
            if self._connection_string:
                self._client = BlobServiceClient.from_connection_string(self._connection_string)
            elif self._sas_token and self._account_name:
                account_url = f"https://{self._account_name}.blob.core.windows.net"
                self._client = BlobServiceClient(account_url=account_url, credential=self._sas_token)

    async def get_auth_url(self, state: str) -> str:
        raise ConnectorError("Azure Blob uses API key auth, not OAuth")

    async def exchange_code(self, auth_code: str, redirect_uri: str) -> Dict[str, Any]:
        raise ConnectorError("Azure Blob uses API key auth, not OAuth")

    async def refresh_token(self, refresh_token_str: str) -> Dict[str, Any]:
        return {}

    async def revoke_token(self, token: str) -> None:
        pass

    async def health_check(self) -> Dict[str, Any]:
        if not self._client:
            return {"status": "error", "message": "Not authenticated"}
        try:
            list(self._client.list_containers(max_results=1))
            return {"status": "ok"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def full_sync(self) -> AsyncIterator[ConnectorFileMetadata]:
        if not self._client:
            raise ConnectorAuthError("Not authenticated")

        containers_to_scan = self._containers or self._list_all_containers()

        for container_name in containers_to_scan:
            container_client = self._client.get_container_client(container_name)
            for blob in container_client.list_blobs():
                blob_dict = {
                    "name": blob.name,
                    "size": blob.size,
                    "etag": blob.etag,
                    "last_modified": blob.last_modified,
                    "content_type": blob.content_settings.content_type if blob.content_settings else "",
                }
                if is_indexable(blob.name):
                    yield map_azure_blob(container_name, blob_dict)

    def _list_all_containers(self) -> List[str]:
        return [c["name"] for c in self._client.list_containers()]

    async def incremental_sync(self, cursor: SyncCursor) -> AsyncIterator[ConnectorFileMetadata]:
        # Azure Blob incremental sync is event-driven via Event Grid
        async for item in self.full_sync():
            yield item

    async def detect_deletes(self, cursor: SyncCursor) -> AsyncIterator[str]:
        for x in []:
            yield x

    def process_event_grid_event(self, event: Dict[str, Any]) -> Optional[ConnectorFileMetadata]:
        """
        Process a single Azure Event Grid event for BlobCreated or BlobDeleted.
        Returns ConnectorFileMetadata for creates/updates, None for deletes.
        Caller should tombstone azure://{container}/{blob_name} on None.
        """
        parsed = map_azure_event_grid(event)
        action = parsed["action"]
        container = parsed["container"]
        blob_name = parsed["blob_name"]

        if action == "delete":
            return None

        if not is_indexable(blob_name):
            return None

        return map_azure_blob(container, {
            "name": blob_name,
            "size": parsed["content_length"],
            "etag": parsed["etag"],
            "last_modified": "",
            "content_type": parsed["content_type"],
        })

    async def download_file(self, file_id: str) -> bytes:
        """Download a blob. file_id format: azure://container/blob_name"""
        if not self._client:
            raise ConnectorAuthError("Not authenticated")

        if not file_id.startswith("azure://"):
            raise ConnectorError(f"Invalid Azure Blob file_id: {file_id}")

        rest = file_id[8:]
        container, _, blob_name = rest.partition("/")
        if not container or not blob_name:
            raise ConnectorError(f"Could not parse container/blob from: {file_id}")

        blob_client = self._client.get_blob_client(container=container, blob=blob_name)
        stream = blob_client.download_blob()
        return stream.readall()

    async def get_permissions(self, file_id: str) -> List[Dict[str, Any]]:
        return []
