"""
Google Cloud Storage (GCS) Connector Adapter
----------------------------------------------
Authentication: Service account JSON key credentials.
Full Sync: Iterates all objects in configured buckets via list_blobs().
Incremental Sync: Event-driven via GCS Pub/Sub notifications (OBJECT_FINALIZE/OBJECT_DELETE).
  - process_pubsub_message() handles individual Pub/Sub messages dispatched by the orchestrator.
"""

import logging
import os
from typing import AsyncIterator, Dict, Any, List, Optional

from connectors.base.connector import BaseConnector
from connectors.base.metadata import ConnectorFileMetadata
from connectors.base.sync import SyncCursor
from connectors.base.capabilities import CapabilitySet, Capability
from connectors.base.exceptions import ConnectorError, ConnectorAuthError

from .mapper import map_gcs_object, map_pubsub_notification, is_indexable

logger = logging.getLogger(__name__)

try:
    from google.cloud import storage as gcs_storage
    from google.oauth2 import service_account
    GCS_SDK_AVAILABLE = True
except ImportError:
    GCS_SDK_AVAILABLE = False
    gcs_storage = None  # type: ignore
    service_account = None  # type: ignore


class GCSAdapter(BaseConnector):
    """
    Google Cloud Storage connector.
    Uses service account credentials (not OAuth).
    """

    def __init__(self):
        self._credentials_json: Optional[Dict[str, Any]] = None
        self._project_id: Optional[str] = None
        self._buckets: List[str] = []
        self._client = None

    @property
    def provider_name(self) -> str:
        return "gcs"

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
            {"name": "service_account_json", "label": "Service Account JSON (paste contents)", "type": "password", "required": True},
            {"name": "project_id", "label": "Google Cloud Project ID", "type": "text", "required": True},
        ]

    async def authenticate(self, credentials: Dict[str, Any]) -> None:
        self._credentials_json = credentials.get("service_account_json")
        self._project_id = credentials.get("project_id")
        self._buckets = credentials.get("buckets", [])

        if not self._credentials_json and not self._project_id:
            raise ConnectorAuthError(
                "GCSAdapter requires service_account_json or project_id for ADC"
            )

        if GCS_SDK_AVAILABLE:
            if self._credentials_json:
                creds = service_account.Credentials.from_service_account_info(
                    self._credentials_json,
                    scopes=["https://www.googleapis.com/auth/cloud-platform"],
                )
                self._client = gcs_storage.Client(
                    project=self._project_id, credentials=creds
                )
            else:
                # Fall back to Application Default Credentials
                self._client = gcs_storage.Client(project=self._project_id)

    async def get_auth_url(self, state: str) -> str:
        raise ConnectorError("GCS uses service account auth, not OAuth")

    async def exchange_code(self, auth_code: str, redirect_uri: str) -> Dict[str, Any]:
        raise ConnectorError("GCS uses service account auth, not OAuth")

    async def refresh_token(self, refresh_token_str: str) -> Dict[str, Any]:
        return {}

    async def revoke_token(self, token: str) -> None:
        pass

    async def health_check(self) -> Dict[str, Any]:
        if not self._client:
            return {"status": "error", "message": "Not authenticated"}
        try:
            list(self._client.list_buckets(max_results=1))
            return {"status": "ok"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def full_sync(self) -> AsyncIterator[ConnectorFileMetadata]:
        if not self._client:
            raise ConnectorAuthError("Not authenticated")

        buckets_to_scan = self._buckets or self._list_all_buckets()

        for bucket_name in buckets_to_scan:
            bucket = self._client.bucket(bucket_name)
            for blob in self._client.list_blobs(bucket):
                if is_indexable(blob.name):
                    blob_dict = {
                        "name": blob.name,
                        "size": blob.size,
                        "etag": blob.etag,
                        "updated": str(blob.updated),
                        "contentType": blob.content_type,
                    }
                    yield map_gcs_object(bucket_name, blob_dict)

    def _list_all_buckets(self) -> List[str]:
        return [b.name for b in self._client.list_buckets()]

    async def incremental_sync(self, cursor: SyncCursor) -> AsyncIterator[ConnectorFileMetadata]:
        # GCS incremental sync is event-driven via Pub/Sub
        async for item in self.full_sync():
            yield item

    async def detect_deletes(self, cursor: SyncCursor) -> AsyncIterator[str]:
        for x in []:
            yield x

    def process_pubsub_message(self, message: Dict[str, Any]) -> Optional[ConnectorFileMetadata]:
        """
        Process a single GCS Pub/Sub notification message.
        Returns ConnectorFileMetadata for OBJECT_FINALIZE events, None for deletes.
        Caller should tombstone gs://{bucket}/{object_name} on None.
        """
        parsed = map_pubsub_notification(message)
        action = parsed["action"]
        bucket = parsed["bucket"]
        object_name = parsed["object_name"]

        if action == "delete":
            return None

        if not is_indexable(object_name):
            return None

        return map_gcs_object(bucket, {
            "name": object_name,
            "size": parsed["size"],
            "etag": "",
            "updated": "",
            "contentType": parsed["content_type"],
        })

    async def download_file(self, file_id: str) -> bytes:
        """Download a GCS object. file_id format: gs://bucket/object_name"""
        if not self._client:
            raise ConnectorAuthError("Not authenticated")

        if not file_id.startswith("gs://"):
            raise ConnectorError(f"Invalid GCS file_id: {file_id}")

        rest = file_id[5:]
        bucket_name, _, object_name = rest.partition("/")
        if not bucket_name or not object_name:
            raise ConnectorError(f"Could not parse bucket/object from: {file_id}")

        bucket = self._client.bucket(bucket_name)
        blob = bucket.blob(object_name)
        return blob.download_as_bytes()

    async def get_permissions(self, file_id: str) -> List[Dict[str, Any]]:
        return []
