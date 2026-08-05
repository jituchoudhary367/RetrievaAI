"""
S3 Connector Adapter
--------------------
Authentication: AWS credentials (access_key_id + secret_access_key + optional session_token).
Full Sync: Iterates all objects in configured buckets via list_objects_v2 pagination.
Incremental Sync: Consumes S3 Event Notifications delivered via SQS.
  - Caller is responsible for polling SQS and passing event records to process_event_record().
  - This adapter does NOT poll SQS directly (separation of concerns: the orchestrator's
    event consumer calls process_event_record per message).
"""

import logging
import os
from typing import AsyncIterator, Dict, Any, List, Optional

import httpx

from connectors.base.connector import BaseConnector
from connectors.base.metadata import ConnectorFileMetadata
from connectors.base.sync import SyncCursor
from connectors.base.capabilities import CapabilitySet, Capability
from connectors.base.exceptions import ConnectorError, ConnectorAuthError

from .mapper import map_s3_object, map_s3_event, is_indexable

logger = logging.getLogger(__name__)

# S3 uses boto3 in real deployments; here we abstract the API so tests can mock it.
try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    boto3 = None  # type: ignore


class S3Adapter(BaseConnector):
    """
    AWS S3 connector.  Uses AWS credentials (not OAuth).
    """

    def __init__(self):
        self._aws_access_key_id: Optional[str] = None
        self._aws_secret_access_key: Optional[str] = None
        self._aws_session_token: Optional[str] = None
        self._region: str = "us-east-1"
        self._buckets: List[str] = []
        self._client = None

    @property
    def provider_name(self) -> str:
        return "s3"

    def capabilities(self) -> CapabilitySet:
        return {
            Capability.API_KEY_AUTH,
            Capability.INCREMENTAL_SYNC,
            Capability.CHANGE_NOTIFICATIONS,
            Capability.METADATA_EXTRACTION,
            Capability.BINARY_FILE_SUPPORT,
            Capability.DELETE_EVENTS,
        }

    async def authenticate(self, credentials: Dict[str, Any]) -> None:
        self._aws_access_key_id = credentials.get("aws_access_key_id")
        self._aws_secret_access_key = credentials.get("aws_secret_access_key")
        self._aws_session_token = credentials.get("aws_session_token")
        self._region = credentials.get("region", "us-east-1")
        self._buckets = credentials.get("buckets", [])

        if not self._aws_access_key_id or not self._aws_secret_access_key:
            raise ConnectorAuthError("S3Adapter requires aws_access_key_id and aws_secret_access_key")

        if BOTO3_AVAILABLE:
            self._client = boto3.client(
                "s3",
                aws_access_key_id=self._aws_access_key_id,
                aws_secret_access_key=self._aws_secret_access_key,
                aws_session_token=self._aws_session_token,
                region_name=self._region,
            )

    async def get_auth_url(self, state: str) -> str:
        raise ConnectorError("S3 uses API key auth, not OAuth")

    async def exchange_code(self, auth_code: str, redirect_uri: str) -> Dict[str, Any]:
        raise ConnectorError("S3 uses API key auth, not OAuth")

    async def refresh_token(self, refresh_token_str: str) -> Dict[str, Any]:
        return {}

    async def revoke_token(self, token: str) -> None:
        pass

    async def health_check(self) -> Dict[str, Any]:
        if not self._client:
            return {"status": "error", "message": "Not authenticated"}
        try:
            self._client.list_buckets()
            return {"status": "ok"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def full_sync(self) -> AsyncIterator[ConnectorFileMetadata]:
        if not self._client:
            raise ConnectorAuthError("Not authenticated")

        buckets_to_scan = self._buckets or self._list_all_buckets()

        for bucket in buckets_to_scan:
            paginator = self._client.get_paginator("list_objects_v2")
            for page in paginator.paginate(Bucket=bucket):
                for obj in page.get("Contents", []):
                    key = obj.get("Key", "")
                    if is_indexable(key):
                        yield map_s3_object(bucket, obj)

    def _list_all_buckets(self) -> List[str]:
        response = self._client.list_buckets()
        return [b["Name"] for b in response.get("Buckets", [])]

    async def incremental_sync(self, cursor: SyncCursor) -> AsyncIterator[ConnectorFileMetadata]:
        # S3 incremental sync is event-driven; callers should use process_event_record()
        async for item in self.full_sync():
            yield item

    async def detect_deletes(self, cursor: SyncCursor) -> AsyncIterator[str]:
        # Deletes come via event records, not polling
        for x in []:
            yield x

    def process_event_record(self, event_record: Dict[str, Any]) -> Optional[ConnectorFileMetadata]:
        """
        Process a single S3 Event Notification record.
        Returns ConnectorFileMetadata for puts, or None for deletes
        (delete events are handled by returning the external_id that should be tombstoned).
        """
        parsed = map_s3_event(event_record)
        action = parsed["action"]
        key = parsed["key"]
        bucket = parsed["bucket"]

        if action == "delete":
            return None  # Caller should tombstone f"s3://{bucket}/{key}"

        if not is_indexable(key):
            return None

        return map_s3_object(bucket, {
            "Key": key,
            "Size": parsed["size"],
            "ETag": parsed["etag"],
            "LastModified": "",
        })

    async def download_file(self, file_id: str) -> bytes:
        """Download an object from S3. file_id format: s3://bucket/key"""
        if not self._client:
            raise ConnectorAuthError("Not authenticated")

        if not file_id.startswith("s3://"):
            raise ConnectorError(f"Invalid S3 file_id: {file_id}")

        rest = file_id[5:]
        bucket, _, key = rest.partition("/")
        if not bucket or not key:
            raise ConnectorError(f"Could not parse bucket/key from: {file_id}")

        response = self._client.get_object(Bucket=bucket, Key=key)
        return response["Body"].read()

    async def get_permissions(self, file_id: str) -> List[Dict[str, Any]]:
        return []
