import pytest
from unittest.mock import MagicMock

from connectors.gcs.mapper import (
    map_gcs_object,
    map_pubsub_notification,
    is_indexable,
)
from connectors.gcs.adapter import GCSAdapter


# ---- mapper tests ----

def test_is_indexable_allows_text():
    assert is_indexable("README.md") is True
    assert is_indexable("config.yaml") is True
    assert is_indexable("schema.json") is True

def test_is_indexable_blocks_binary():
    assert is_indexable("photo.jpg") is False
    assert is_indexable("archive.tar.gz") is False
    assert is_indexable("model.dll") is False

def test_map_gcs_object():
    blob = {
        "name": "datasets/train.csv",
        "size": 2048000,
        "etag": "CKqLv8qg...",
        "updated": "2024-05-10T09:00:00Z",
        "contentType": "text/csv",
    }
    cf = map_gcs_object("ml-data-bucket", blob)
    assert cf.external_id == "gs://ml-data-bucket/datasets/train.csv"
    assert cf.name == "train.csv"
    assert cf.mime_type == "text/csv"
    assert cf.size_bytes == 2048000
    assert cf.external_path == "/ml-data-bucket/datasets/train.csv"
    assert cf.raw_metadata["bucket"] == "ml-data-bucket"
    assert cf.raw_metadata["object_name"] == "datasets/train.csv"

def test_map_gcs_object_infers_mime_from_extension():
    blob = {
        "name": "notes.md",
        "size": 100,
        "etag": "",
        "updated": "",
        "contentType": "application/octet-stream",
    }
    cf = map_gcs_object("my-bucket", blob)
    assert cf.mime_type == "text/markdown"

def test_map_pubsub_notification_finalize():
    message = {
        "attributes": {
            "eventType": "OBJECT_FINALIZE",
            "bucketId": "prod-docs",
            "objectId": "reports/annual.pdf",
            "objectSize": "512000",
            "contentType": "application/pdf",
        }
    }
    parsed = map_pubsub_notification(message)
    assert parsed["action"] == "put"
    assert parsed["bucket"] == "prod-docs"
    assert parsed["object_name"] == "reports/annual.pdf"
    assert parsed["size"] == 512000

def test_map_pubsub_notification_delete():
    message = {
        "attributes": {
            "eventType": "OBJECT_DELETE",
            "bucketId": "prod-docs",
            "objectId": "old/file.txt",
            "objectSize": "0",
            "contentType": "",
        }
    }
    parsed = map_pubsub_notification(message)
    assert parsed["action"] == "delete"

def test_map_pubsub_notification_archive():
    message = {
        "attributes": {
            "eventType": "OBJECT_ARCHIVE",
            "bucketId": "cold-storage",
            "objectId": "archive/data.parquet",
            "objectSize": "0",
            "contentType": "",
        }
    }
    parsed = map_pubsub_notification(message)
    assert parsed["action"] == "delete"


# ---- adapter unit tests ----

@pytest.fixture
def gcs_adapter_with_mock():
    adapter = GCSAdapter()
    adapter._project_id = "fake-project"
    adapter._buckets = ["test-bucket"]
    mock_client = MagicMock()
    adapter._client = mock_client
    return adapter, mock_client

def test_process_pubsub_message_finalize(gcs_adapter_with_mock):
    adapter, _ = gcs_adapter_with_mock
    message = {
        "attributes": {
            "eventType": "OBJECT_FINALIZE",
            "bucketId": "test-bucket",
            "objectId": "docs/spec.md",
            "objectSize": "1024",
            "contentType": "text/markdown",
        }
    }
    result = adapter.process_pubsub_message(message)
    assert result is not None
    assert result.external_id == "gs://test-bucket/docs/spec.md"

def test_process_pubsub_message_delete_returns_none(gcs_adapter_with_mock):
    adapter, _ = gcs_adapter_with_mock
    message = {
        "attributes": {
            "eventType": "OBJECT_DELETE",
            "bucketId": "test-bucket",
            "objectId": "docs/old.md",
            "objectSize": "0",
            "contentType": "",
        }
    }
    result = adapter.process_pubsub_message(message)
    assert result is None  # Caller tombstones gs://test-bucket/docs/old.md

def test_process_pubsub_message_binary_skipped(gcs_adapter_with_mock):
    adapter, _ = gcs_adapter_with_mock
    message = {
        "attributes": {
            "eventType": "OBJECT_FINALIZE",
            "bucketId": "assets",
            "objectId": "logo.png",
            "objectSize": "100000",
            "contentType": "image/png",
        }
    }
    result = adapter.process_pubsub_message(message)
    assert result is None  # Binary not indexed
