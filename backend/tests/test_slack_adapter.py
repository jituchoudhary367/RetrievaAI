import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timezone
import httpx

from connectors.slack.adapter import SlackAdapter
from connectors.slack.mapper import map_slack_thread, map_slack_attachment
from connectors.base.exceptions import ConnectorRateLimitError

@pytest.fixture
def slack_adapter():
    adapter = SlackAdapter()
    return adapter

def test_map_slack_thread():
    messages = [
        {"user": "U123", "ts": "1700000000.000000", "text": "Hello team, please review this PR.", "thread_ts": "1700000000.000000"},
        {"user": "U456", "ts": "1700000010.000000", "text": "Looks good to me.", "thread_ts": "1700000000.000000", "files": [{"id": "F1", "name": "screenshot.png", "url_private": "https://slack.com/files/screenshot.png"}]}
    ]
    
    cf = map_slack_thread("1700000000.000000", "C123", messages)
    
    assert cf.external_id == "1700000000.000000"
    assert cf.name == "Hello team, please review this PR."
    assert cf.mime_type == "text/markdown"
    assert cf.external_path == "/channels/C123"
    assert cf.raw_metadata["channel_id"] == "C123"
    assert cf.raw_metadata["thread_ts"] == "1700000000.000000"
    
    md = cf.raw_metadata["markdown_content"]
    assert "Hello team, please review this PR." in md
    assert "U123" in md
    assert "U456" in md
    assert "Looks good to me." in md
    assert "screenshot.png" in md
    assert "https://slack.com/files/screenshot.png" in md

def test_map_slack_attachment():
    file_obj = {
        "id": "F999",
        "name": "design.pdf",
        "mimetype": "application/pdf",
        "size": 1024,
        "url_private": "https://slack.com/files/design.pdf"
    }
    
    cf = map_slack_attachment(file_obj, "C123", "1700000000.000000")
    
    assert cf.external_id == "file_F999"
    assert cf.name == "design.pdf"
    assert cf.mime_type == "application/pdf"
    assert cf.size_bytes == 1024
    assert cf.external_path == "/channels/C123/1700000000.000000"
    assert cf.raw_metadata["type"] == "attachment"
    assert cf.raw_metadata["file_id"] == "F999"

@pytest.mark.asyncio
@patch("connectors.slack.adapter.exchange_code")
async def test_exchange_code(mock_exchange, slack_adapter):
    mock_exchange.return_value = (
        {
            "access_token": "xoxp-123",
            "provider_user_id": "U123",
            "team_id": "T123"
        },
        datetime.now(timezone.utc)
    )
    
    data = await slack_adapter.exchange_code("auth-code", "http://localhost")
    
    assert data["access_token"] == "xoxp-123"
    assert data["provider_user_id"] == "U123"
    assert data["team_id"] == "T123"

@pytest.mark.asyncio
@patch("httpx.AsyncClient.get")
@patch("connectors.slack.adapter.asyncio.sleep")
async def test_api_call_rate_limit(mock_sleep, mock_get, slack_adapter):
    slack_adapter._access_token = "xoxp-123"
    
    mock_resp_429 = MagicMock()
    mock_resp_429.status_code = 429
    mock_resp_429.headers = {"Retry-After": "2"}
    
    mock_resp_200 = MagicMock()
    mock_resp_200.status_code = 200
    mock_resp_200.json.return_value = {"ok": True, "channels": []}
    mock_resp_200.raise_for_status = MagicMock()
    
    # First call returns 429, second returns 200
    mock_get.side_effect = [mock_resp_429, mock_resp_200]
    
    data = await slack_adapter._api_call("conversations.list")
    
    assert mock_sleep.call_count == 1
    mock_sleep.assert_called_with(2)
    assert data["ok"] is True

@pytest.mark.asyncio
@patch("httpx.AsyncClient.get")
@patch("connectors.slack.adapter.asyncio.sleep")
async def test_api_call_rate_limit_failure(mock_sleep, mock_get, slack_adapter):
    slack_adapter._access_token = "xoxp-123"
    
    mock_resp_429 = MagicMock()
    mock_resp_429.status_code = 429
    mock_resp_429.headers = {"Retry-After": "1"}
    
    # Always returns 429
    mock_get.return_value = mock_resp_429
    
    with pytest.raises(ConnectorRateLimitError):
        await slack_adapter._api_call("conversations.list")
        
    assert mock_sleep.call_count == 3
