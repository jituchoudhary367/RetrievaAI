import hashlib
import hmac
import json
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timezone

from connectors.dropbox.adapter import DropboxAdapter
from connectors.dropbox.mapper import (
    map_dropbox_file,
    map_dropbox_deleted,
    is_indexable,
)
from connectors.base.exceptions import ConnectorRateLimitError

# We test the webhook route's signature verification logic directly too
from api.routes.webhooks.dropbox import _verify_signature

FAKE_SECRET = "test-dropbox-secret"


# ---- mapper tests (sync) ----

def test_is_indexable_text_files():
    assert is_indexable("/notes/readme.md") is True
    assert is_indexable("/src/app.py") is True
    assert is_indexable("/data/report.csv") is True


def test_is_indexable_blocks_binaries():
    assert is_indexable("/images/logo.png") is False
    assert is_indexable("/builds/app.exe") is False
    assert is_indexable("/fonts/Inter.woff2") is False


def test_map_dropbox_file():
    entry = {
        ".tag": "file",
        "name": "design_doc.md",
        "path_lower": "/work/design_doc.md",
        "id": "id:abc123xyz",
        "size": 2048,
        "server_modified": "2024-06-01T10:00:00Z",
        "content_hash": "deadbeef",
    }
    cf = map_dropbox_file(entry)

    assert cf.external_id == "id:abc123xyz"
    assert cf.name == "design_doc.md"
    assert cf.mime_type == "text/markdown"
    assert cf.size_bytes == 2048
    assert cf.external_path == "/work/design_doc.md"
    assert cf.raw_metadata["content_hash"] == "deadbeef"
    assert cf.raw_metadata["server_modified"] == "2024-06-01T10:00:00Z"


def test_map_dropbox_file_unknown_extension():
    entry = {
        ".tag": "file",
        "name": "data.bin",
        "path_lower": "/misc/data.bin",
        "id": "id:zzz999",
        "size": 512,
        "server_modified": "2024-01-01T00:00:00Z",
    }
    cf = map_dropbox_file(entry)
    assert cf.mime_type == "application/octet-stream"


def test_map_dropbox_deleted():
    entry = {
        ".tag": "deleted",
        "path_lower": "/work/old_file.txt",
    }
    result = map_dropbox_deleted(entry)
    assert result == "/work/old_file.txt"


# ---- webhook signature tests ----

def _make_signature(body: bytes, secret: str) -> str:
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def test_valid_signature_accepted():
    body = b'{"list_folder": {"accounts": ["dbid:abc"]}}'
    sig = _make_signature(body, FAKE_SECRET)
    with patch("api.routes.webhooks.dropbox.DROPBOX_APP_SECRET", FAKE_SECRET):
        assert _verify_signature(body, sig) is True


def test_invalid_signature_rejected():
    body = b'{"list_folder": {"accounts": ["dbid:abc"]}}'
    with patch("api.routes.webhooks.dropbox.DROPBOX_APP_SECRET", FAKE_SECRET):
        assert _verify_signature(body, "badsignature") is False


def test_empty_signature_rejected():
    body = b'{"list_folder": {"accounts": []}}'
    with patch("api.routes.webhooks.dropbox.DROPBOX_APP_SECRET", FAKE_SECRET):
        assert _verify_signature(body, "") is False


def test_tampered_body_rejected():
    original_body = b'{"list_folder": {"accounts": ["dbid:abc"]}}'
    tampered_body = b'{"list_folder": {"accounts": ["dbid:ATTACKER"]}}'
    sig = _make_signature(original_body, FAKE_SECRET)
    with patch("api.routes.webhooks.dropbox.DROPBOX_APP_SECRET", FAKE_SECRET):
        assert _verify_signature(tampered_body, sig) is False


# ---- adapter tests ----

@pytest.fixture
def dropbox_adapter():
    adapter = DropboxAdapter()
    adapter._access_token = "sl.test_token"
    adapter._refresh_token = "test_refresh"
    return adapter


@pytest.mark.asyncio
@patch("connectors.dropbox.adapter.asyncio.sleep", new_callable=AsyncMock)
@patch("httpx.AsyncClient.post", new_callable=AsyncMock)
async def test_rate_limit_backoff(mock_post, mock_sleep, dropbox_adapter):
    """Test that a 429 response triggers a sleep + retry."""
    mock_429 = MagicMock()
    mock_429.status_code = 429
    mock_429.headers = {"Retry-After": "3"}

    mock_200 = MagicMock()
    mock_200.status_code = 200
    mock_200.json.return_value = {"entries": [], "has_more": False, "cursor": "cur_abc"}
    mock_200.raise_for_status = MagicMock()

    mock_post.side_effect = [mock_429, mock_200]

    data = await dropbox_adapter._post("https://api.dropboxapi.com/2/files/list_folder", {"path": ""})
    assert data["cursor"] == "cur_abc"
    mock_sleep.assert_called_once_with(3)


@pytest.mark.asyncio
@patch("connectors.dropbox.adapter.asyncio.sleep", new_callable=AsyncMock)
@patch("httpx.AsyncClient.post", new_callable=AsyncMock)
async def test_rate_limit_max_retries_raises(mock_post, mock_sleep, dropbox_adapter):
    """Test that exhausted retries raises ConnectorRateLimitError."""
    mock_429 = MagicMock()
    mock_429.status_code = 429
    mock_429.headers = {"Retry-After": "1"}
    mock_post.return_value = mock_429

    with pytest.raises(ConnectorRateLimitError):
        await dropbox_adapter._post("https://api.dropboxapi.com/2/files/list_folder", {})

    assert mock_sleep.call_count == 3
