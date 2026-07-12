import pytest
import pytest_asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime, timezone

from connectors.onedrive.adapter import OneDriveAdapter
from connectors.onedrive.mapper import map_onedrive_item
from connectors.base.exceptions import ConnectorAuthError

@pytest.fixture
def onedrive_adapter():
    return OneDriveAdapter()

def test_map_onedrive_item():
    raw_item = {
        "id": "file-1",
        "name": "test.txt",
        "file": {"mimeType": "text/plain"},
        "size": 1024
    }
    
    cf = map_onedrive_item(raw_item)
    
    assert cf.external_id == "file-1"
    assert cf.name == "test.txt"
    assert cf.mime_type == "text/plain"
    assert cf.size_bytes == 1024
    assert cf.raw_metadata["id"] == "file-1"

@pytest.mark.asyncio
async def test_get_auth_url(onedrive_adapter):
    url = await onedrive_adapter.get_auth_url("state-123")
    assert "login.microsoftonline.com" in url
    assert "state=state-123" in url
    assert "client_id" in url

@pytest.mark.asyncio
@patch("connectors.onedrive.adapter.exchange_code")
@patch("httpx.AsyncClient.get")
async def test_exchange_code(mock_get, mock_exchange, onedrive_adapter):
    mock_exchange.return_value = ({"access_token": "acc", "refresh_token": "ref"}, datetime.now(timezone.utc))
    
    mock_resp = MagicMock()
    mock_resp.is_success = True
    mock_resp.json.return_value = {"id": "user-1", "userPrincipalName": "test@example.com"}
    mock_get.return_value = mock_resp
    
    data = await onedrive_adapter.exchange_code("auth-code", "http://localhost")
    
    assert data["access_token"] == "acc"
    assert data["provider_user_id"] == "user-1"
    assert data["provider_email"] == "test@example.com"
