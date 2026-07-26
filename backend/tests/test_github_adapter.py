import pytest
import asyncio
import base64
import time
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timezone

from connectors.github.adapter import GithubAdapter
from connectors.github.mapper import (
    map_github_file,
    map_github_release,
    is_indexable_file,
)
from connectors.base.exceptions import ConnectorRateLimitError


@pytest.fixture
def github_adapter():
    adapter = GithubAdapter()
    adapter._access_token = "gho_test_token"
    return adapter


# ---- mapper tests (sync) ----

def test_is_indexable_file_allows_text():
    assert is_indexable_file("README.md") is True
    assert is_indexable_file("main.py") is True
    assert is_indexable_file("config.yaml") is True
    assert is_indexable_file("notes.txt") is True


def test_is_indexable_file_blocks_binary():
    assert is_indexable_file("image.png") is False
    assert is_indexable_file("archive.zip") is False
    assert is_indexable_file("library.dll") is False
    assert is_indexable_file("font.woff2") is False


def test_map_github_file():
    item = {
        "path": "src/main.py",
        "sha": "abc123",
        "size": 1024,
        "type": "blob",
        "url": "https://api.github.com/repos/user/repo/git/blobs/abc123"
    }
    cf = map_github_file(item, "user/repo")

    assert cf.external_id == "repo:user/repo:blob:abc123"
    assert cf.name == "main.py"
    assert cf.external_path == "/user/repo/src/main.py"
    assert cf.raw_metadata["repo"] == "user/repo"
    assert cf.raw_metadata["sha"] == "abc123"
    assert cf.raw_metadata["path"] == "src/main.py"


def test_map_github_release():
    release = {
        "id": 9999,
        "tag_name": "v1.0.0",
        "name": "Initial Release",
        "body": "## Changelog\n- First release",
        "published_at": "2024-01-01T00:00:00Z"
    }
    cf = map_github_release(release, "user/repo")

    assert cf.external_id == "repo:user/repo:release:9999"
    assert cf.name == "Release: Initial Release"
    assert cf.mime_type == "text/markdown"
    assert cf.size_bytes > 0
    assert cf.raw_metadata["tag_name"] == "v1.0.0"
    assert cf.raw_metadata["type"] == "release"
    assert "markdown_content" in cf.raw_metadata


def test_map_github_release_fallback_name():
    release = {
        "id": 1001,
        "tag_name": "v0.1.0",
        "name": None,
        "body": "",
        "published_at": "2024-01-01T00:00:00Z"
    }
    cf = map_github_release(release, "user/repo")
    assert cf.name == "Release: v0.1.0"


# ---- adapter tests (async) ----

@pytest.mark.asyncio
@patch("connectors.github.adapter.asyncio.sleep", new_callable=AsyncMock)
@patch("httpx.AsyncClient.get", new_callable=AsyncMock)
async def test_api_call_rate_limit_retry(mock_get, mock_sleep, github_adapter):
    """Test that a 403 with zero remaining triggers a sleep and retry."""
    reset_ts = str(int(time.time()) + 5)

    mock_resp_limited = MagicMock()
    mock_resp_limited.status_code = 403
    mock_resp_limited.headers = {
        "X-RateLimit-Remaining": "0",
        "X-RateLimit-Reset": reset_ts,
    }

    mock_resp_ok = MagicMock()
    mock_resp_ok.status_code = 200
    mock_resp_ok.headers = {"X-RateLimit-Remaining": "100"}
    mock_resp_ok.json.return_value = {"login": "user"}
    mock_resp_ok.raise_for_status = MagicMock()

    mock_get.side_effect = [mock_resp_limited, mock_resp_ok]

    result = await github_adapter._api_call("user")

    assert mock_sleep.call_count == 1
    assert result["login"] == "user"


@pytest.mark.asyncio
@patch("connectors.github.adapter.asyncio.sleep", new_callable=AsyncMock)
@patch("httpx.AsyncClient.get", new_callable=AsyncMock)
async def test_api_call_rate_limit_max_exceeded(mock_get, mock_sleep, github_adapter):
    """Test that exhausting all retries raises ConnectorRateLimitError."""
    mock_resp_limited = MagicMock()
    mock_resp_limited.status_code = 429
    mock_resp_limited.headers = {
        "X-RateLimit-Remaining": "0",
        "X-RateLimit-Reset": "1",
    }
    mock_get.return_value = mock_resp_limited

    with pytest.raises(ConnectorRateLimitError):
        await github_adapter._api_call("repos")

    assert mock_sleep.call_count == 3


@pytest.mark.asyncio
@patch("httpx.AsyncClient.get", new_callable=AsyncMock)
async def test_download_file_release_from_cache(mock_get, github_adapter):
    """Test that a release document is served from the in-memory cache."""
    release_id = "repo:user/repo:release:9999"
    github_adapter._release_cache[release_id] = "## Changelog\n- First release"

    content = await github_adapter.download_file(release_id)
    assert content == b"## Changelog\n- First release"
    # Should NOT have made any HTTP calls
    assert mock_get.call_count == 0


@pytest.mark.asyncio
@patch("httpx.AsyncClient.get", new_callable=AsyncMock)
async def test_download_file_blob(mock_get, github_adapter):
    """Test downloading a code blob via the GitHub Blobs API."""
    raw_content = b"print('Hello World')"
    b64_content = base64.b64encode(raw_content).decode("utf-8")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {"X-RateLimit-Remaining": "4000"}
    mock_resp.json.return_value = {"content": b64_content, "encoding": "base64"}
    mock_resp.raise_for_status = MagicMock()
    mock_get.return_value = mock_resp

    file_id = "repo:user/repo:blob:abc123"
    content = await github_adapter.download_file(file_id)
    assert content == raw_content
