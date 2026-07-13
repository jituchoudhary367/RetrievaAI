import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

from connectors.sharepoint.adapter import SharePointAdapter
from connectors.sharepoint.mapper import map_sharepoint_item

@pytest.fixture
def sharepoint_adapter():
    return SharePointAdapter()

def test_map_sharepoint_item():
    raw_item = {
        "id": "file-1",
        "name": "test.txt",
        "file": {"mimeType": "text/plain"},
        "size": 1024,
        "parentReference": {
            "path": "/drive/root:/Documents/ProjectX"
        }
    }
    
    cf = map_sharepoint_item(raw_item, "site-1", "list-1")
    
    assert cf.external_id == "file-1"
    assert cf.name == "test.txt"
    assert cf.mime_type == "text/plain"
    assert cf.size_bytes == 1024
    assert cf.external_path == "/drive/root:/Documents/ProjectX"
    assert cf.raw_metadata["siteId"] == "site-1"
    assert cf.raw_metadata["listId"] == "list-1"
    assert cf.raw_metadata["id"] == "file-1"

@pytest.mark.asyncio
async def test_get_auth_url(sharepoint_adapter):
    url = await sharepoint_adapter.get_auth_url("state-123")
    assert "login.microsoftonline.com" in url
    assert "state=state-123" in url
    assert "client_id" in url
    assert "Sites.Read.All" in url

@pytest.mark.asyncio
@patch("connectors.sharepoint.adapter.exchange_code")
@patch("httpx.AsyncClient.get")
async def test_exchange_code(mock_get, mock_exchange, sharepoint_adapter):
    mock_exchange.return_value = ({"access_token": "acc", "refresh_token": "ref"}, datetime.now(timezone.utc))
    
    mock_resp = MagicMock()
    mock_resp.is_success = True
    mock_resp.json.return_value = {"id": "user-1", "userPrincipalName": "test@example.com"}
    mock_get.return_value = mock_resp
    
    data = await sharepoint_adapter.exchange_code("auth-code", "http://localhost")
    
    assert data["access_token"] == "acc"
    assert data["provider_user_id"] == "user-1"
    assert data["provider_email"] == "test@example.com"
