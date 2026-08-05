import pytest
from unittest.mock import MagicMock

from connectors.azure_blob.mapper import (
    map_azure_blob,
    map_azure_event_grid,
    is_indexable,
)
from connectors.azure_blob.adapter import AzureBlobAdapter


# ---- mapper tests ----

def test_is_indexable_allows_text():
    assert is_indexable("readme.md") is True
    assert is_indexable("report.pdf") is True
    assert is_indexable("data.csv") is True

def test_is_indexable_blocks_binary():
    assert is_indexable("photo.jpeg") is False
    assert is_indexable("backup.tar.gz") is False
    assert is_indexable("font.woff2") is False

def test_map_azure_blob():
    blob = {
        "name": "reports/q1-2024.csv",
        "size": 8192,
        "etag": '"0x8DC1234"',
        "last_modified": "2024-03-31T00:00:00Z",
        "content_type": "text/csv",
    }
    cf = map_azure_blob("finance-container", blob)
    assert cf.external_id == "azure://finance-container/reports/q1-2024.csv"
    assert cf.name == "q1-2024.csv"
    assert cf.mime_type == "text/csv"
    assert cf.size_bytes == 8192
    assert cf.raw_metadata["container"] == "finance-container"
    assert cf.raw_metadata["blob_name"] == "reports/q1-2024.csv"

def test_map_azure_blob_infers_mime_from_extension():
    blob = {
        "name": "doc.md",
        "size": 512,
        "etag": "",
        "last_modified": "",
        "content_type": "application/octet-stream",  # generic, should be inferred
    }
    cf = map_azure_blob("my-container", blob)
    assert cf.mime_type == "text/markdown"

def test_map_azure_event_grid_blob_created():
    event = {
        "eventType": "Microsoft.Storage.BlobCreated",
        "subject": "/blobServices/default/containers/my-container/blobs/path/to/file.txt",
        "data": {
            "contentLength": 1024,
            "eTag": "0x8FABCDEF",
            "contentType": "text/plain",
        }
    }
    parsed = map_azure_event_grid(event)
    assert parsed["action"] == "put"
    assert parsed["container"] == "my-container"
    assert parsed["blob_name"] == "path/to/file.txt"
    assert parsed["content_length"] == 1024

def test_map_azure_event_grid_blob_deleted():
    event = {
        "eventType": "Microsoft.Storage.BlobDeleted",
        "subject": "/blobServices/default/containers/archive/blobs/old.txt",
        "data": {}
    }
    parsed = map_azure_event_grid(event)
    assert parsed["action"] == "delete"
    assert parsed["container"] == "archive"
    assert parsed["blob_name"] == "old.txt"


# ---- adapter unit tests ----

@pytest.fixture
def azure_adapter_with_mock():
    adapter = AzureBlobAdapter()
    adapter._connection_string = "fake-connection-string"
    adapter._containers = ["test-container"]
    mock_client = MagicMock()
    adapter._client = mock_client
    return adapter, mock_client

def test_process_event_grid_put(azure_adapter_with_mock):
    adapter, _ = azure_adapter_with_mock
    event = {
        "eventType": "Microsoft.Storage.BlobCreated",
        "subject": "/blobServices/default/containers/my-container/blobs/notes.md",
        "data": {"contentLength": 200, "eTag": "abc", "contentType": "text/markdown"},
    }
    result = adapter.process_event_grid_event(event)
    assert result is not None
    assert result.external_id == "azure://my-container/notes.md"

def test_process_event_grid_delete_returns_none(azure_adapter_with_mock):
    adapter, _ = azure_adapter_with_mock
    event = {
        "eventType": "Microsoft.Storage.BlobDeleted",
        "subject": "/blobServices/default/containers/my-container/blobs/notes.md",
        "data": {},
    }
    result = adapter.process_event_grid_event(event)
    assert result is None  # Caller should tombstone

def test_process_event_grid_binary_skipped(azure_adapter_with_mock):
    adapter, _ = azure_adapter_with_mock
    event = {
        "eventType": "Microsoft.Storage.BlobCreated",
        "subject": "/blobServices/default/containers/assets/blobs/logo.png",
        "data": {"contentLength": 50000, "eTag": "", "contentType": "image/png"},
    }
    result = adapter.process_event_grid_event(event)
    assert result is None  # Binary files skipped
