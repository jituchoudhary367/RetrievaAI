import pytest
from unittest.mock import MagicMock, patch

from connectors.s3.mapper import (
    map_s3_object,
    map_s3_event,
    is_indexable,
)
from connectors.s3.adapter import S3Adapter


# ---- mapper tests ----

def test_is_indexable_allows_text():
    assert is_indexable("README.md") is True
    assert is_indexable("data/report.csv") is True
    assert is_indexable("src/main.py") is True

def test_is_indexable_blocks_binary():
    assert is_indexable("logo.png") is False
    assert is_indexable("archive.zip") is False
    assert is_indexable("app.exe") is False

def test_map_s3_object():
    obj = {
        "Key": "docs/spec.md",
        "Size": 4096,
        "ETag": '"abc123"',
        "LastModified": "2024-01-15T10:00:00Z",
    }
    cf = map_s3_object("my-bucket", obj)
    assert cf.external_id == "s3://my-bucket/docs/spec.md"
    assert cf.name == "spec.md"
    assert cf.mime_type == "text/markdown"
    assert cf.size_bytes == 4096
    assert cf.external_path == "/my-bucket/docs/spec.md"
    assert cf.raw_metadata["bucket"] == "my-bucket"
    assert cf.raw_metadata["key"] == "docs/spec.md"
    assert cf.raw_metadata["etag"] == "abc123"  # stripped quotes

def test_map_s3_event_put():
    record = {
        "eventName": "ObjectCreated:Put",
        "s3": {
            "bucket": {"name": "my-bucket"},
            "object": {"key": "data/file.txt", "size": 1024, "eTag": "deadbeef"},
        }
    }
    parsed = map_s3_event(record)
    assert parsed["action"] == "put"
    assert parsed["bucket"] == "my-bucket"
    assert parsed["key"] == "data/file.txt"
    assert parsed["size"] == 1024

def test_map_s3_event_delete():
    record = {
        "eventName": "ObjectRemoved:Delete",
        "s3": {
            "bucket": {"name": "my-bucket"},
            "object": {"key": "old/file.txt", "size": 0, "eTag": ""},
        }
    }
    parsed = map_s3_event(record)
    assert parsed["action"] == "delete"

def test_map_s3_event_url_encoded_key():
    record = {
        "eventName": "ObjectCreated:Put",
        "s3": {
            "bucket": {"name": "my-bucket"},
            "object": {"key": "path+with+spaces/file.txt", "size": 512, "eTag": ""},
        }
    }
    parsed = map_s3_event(record)
    # S3 encodes spaces as + in event notifications
    assert "+" not in parsed["key"]


# ---- adapter unit tests ----

@pytest.fixture
def s3_adapter_with_mock():
    adapter = S3Adapter()
    adapter._aws_access_key_id = "AKIA_FAKE"
    adapter._aws_secret_access_key = "fake_secret"
    adapter._region = "us-east-1"
    adapter._buckets = ["test-bucket"]
    mock_client = MagicMock()
    adapter._client = mock_client
    return adapter, mock_client

def test_process_event_record_put(s3_adapter_with_mock):
    adapter, _ = s3_adapter_with_mock
    record = {
        "eventName": "ObjectCreated:Put",
        "s3": {
            "bucket": {"name": "test-bucket"},
            "object": {"key": "notes.txt", "size": 256, "eTag": "ef01"},
        }
    }
    result = adapter.process_event_record(record)
    assert result is not None
    assert result.external_id == "s3://test-bucket/notes.txt"

def test_process_event_record_delete_returns_none(s3_adapter_with_mock):
    adapter, _ = s3_adapter_with_mock
    record = {
        "eventName": "ObjectRemoved:Delete",
        "s3": {
            "bucket": {"name": "test-bucket"},
            "object": {"key": "notes.txt", "size": 0, "eTag": ""},
        }
    }
    result = adapter.process_event_record(record)
    assert result is None  # Caller should tombstone

def test_process_event_record_binary_skipped(s3_adapter_with_mock):
    adapter, _ = s3_adapter_with_mock
    record = {
        "eventName": "ObjectCreated:Put",
        "s3": {
            "bucket": {"name": "test-bucket"},
            "object": {"key": "image.png", "size": 500000, "eTag": "abc"},
        }
    }
    result = adapter.process_event_record(record)
    assert result is None  # Binary files must not be indexed
