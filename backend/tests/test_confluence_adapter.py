import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

from connectors.confluence.adapter import ConfluenceAdapter
from connectors.confluence.mapper import map_confluence_page, convert_confluence_to_markdown

@pytest.fixture
def confluence_adapter():
    return ConfluenceAdapter()

def test_convert_confluence_to_markdown():
    storage_html = (
        "<h1>Hello World</h1>"
        "<p>This is a <b>bold</b> and <i>italic</i> test.</p>"
        "<p>Here is a <a href=\"https://example.com\">link</a>.</p>"
        "<ul><li>Item 1</li><li>Item 2</li></ul>"
        "<h2>Subheading</h2>"
    )
    
    md = convert_confluence_to_markdown(storage_html)
    
    assert "# Hello World" in md
    assert "**bold**" in md
    assert "*italic*" in md
    assert "[link](https://example.com)" in md
    assert "- Item 1" in md
    assert "- Item 2" in md
    assert "## Subheading" in md

def test_map_confluence_item():
    raw_item = {
        "id": "12345",
        "title": "Project Alpha",
        "body": {
            "storage": {
                "value": "<h1>Alpha</h1>"
            }
        },
        "version": {
            "number": 2
        }
    }
    
    cf = map_confluence_page(raw_item, "ENG")
    
    assert cf.external_id == "12345"
    assert cf.name == "Project Alpha"
    assert cf.mime_type == "text/markdown"
    assert cf.external_path == "/spaces/ENG"
    assert cf.raw_metadata["spaceId"] == "ENG"
    assert cf.raw_metadata["title"] == "Project Alpha"
    assert cf.raw_metadata["version"] == 2

@pytest.mark.asyncio
async def test_get_auth_url(confluence_adapter):
    url = await confluence_adapter.get_auth_url("state-123")
    assert "auth.atlassian.com/authorize" in url
    assert "state=state-123" in url
    assert "client_id" in url
    assert "read:confluence-space.summary" in url

@pytest.mark.asyncio
@patch("connectors.confluence.adapter.exchange_code")
@patch("httpx.AsyncClient.get")
async def test_exchange_code(mock_get, mock_exchange, confluence_adapter):
    mock_exchange.return_value = ({"access_token": "acc", "refresh_token": "ref"}, datetime.now(timezone.utc))
    
    mock_resp = MagicMock()
    mock_resp.is_success = True
    
    # Needs two gets: accessible-resources and user current
    mock_resources_resp = MagicMock()
    mock_resources_resp.json.return_value = [{"id": "cloud-id-1"}]
    mock_resources_resp.is_success = True
    
    mock_user_resp = MagicMock()
    mock_user_resp.json.return_value = {"accountId": "user-1", "email": "test@example.com"}
    mock_user_resp.is_success = True
    
    mock_get.side_effect = [mock_resources_resp, mock_user_resp]
    
    data = await confluence_adapter.exchange_code("auth-code", "http://localhost")
    
    assert data["access_token"] == "acc"
    assert data["cloud_id"] == "cloud-id-1"
    assert data["provider_user_id"] == "user-1"
    assert data["provider_email"] == "test@example.com"
