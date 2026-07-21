import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timezone
from typing import Dict, List, Any

from connectors.notion.adapter import NotionAdapter
from connectors.notion.mapper import (
    map_notion_page,
    blocks_to_markdown,
    MAX_DEPTH,
    _rich_text_to_str,
)


# ---------------------------------------------------------------------------
# Mapper unit tests
# ---------------------------------------------------------------------------

def _rt(text: str, bold: bool = False, italic: bool = False, code: bool = False) -> Dict[str, Any]:
    return {
        "plain_text": text,
        "annotations": {"bold": bold, "italic": italic, "code": code, "strikethrough": False},
        "href": None,
    }


def test_rich_text_plain():
    assert _rich_text_to_str([_rt("hello")]) == "hello"


def test_rich_text_bold():
    assert _rich_text_to_str([_rt("bold", bold=True)]) == "**bold**"


def test_rich_text_italic():
    assert _rich_text_to_str([_rt("em", italic=True)]) == "*em*"


def test_rich_text_code():
    assert _rich_text_to_str([_rt("fn()", code=True)]) == "`fn()`"


def test_blocks_heading():
    blocks = [
        {
            "type": "heading_1",
            "heading_1": {"rich_text": [_rt("Title")]},
            "children": [],
        }
    ]
    md = blocks_to_markdown(blocks)
    assert "# Title" in md


def test_blocks_paragraph():
    blocks = [
        {
            "type": "paragraph",
            "paragraph": {"rich_text": [_rt("Hello world")]},
            "children": [],
        }
    ]
    md = blocks_to_markdown(blocks)
    assert "Hello world" in md


def test_blocks_bulleted_list():
    blocks = [
        {
            "type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": [_rt("Item A")]},
            "children": [],
        },
        {
            "type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": [_rt("Item B")]},
            "children": [],
        },
    ]
    md = blocks_to_markdown(blocks)
    assert "- Item A" in md
    assert "- Item B" in md


def test_blocks_code():
    blocks = [
        {
            "type": "code",
            "code": {"rich_text": [_rt("print('hi')")], "language": "python"},
            "children": [],
        }
    ]
    md = blocks_to_markdown(blocks)
    assert "```python" in md
    assert "print('hi')" in md


def test_blocks_nested_toggle():
    """Toggle parent with nested paragraph child."""
    child = {
        "type": "paragraph",
        "paragraph": {"rich_text": [_rt("nested content")]},
        "children": [],
    }
    blocks = [
        {
            "type": "toggle",
            "toggle": {"rich_text": [_rt("Toggle header")]},
            "children": [child],
        }
    ]
    md = blocks_to_markdown(blocks)
    assert "Toggle header" in md
    assert "nested content" in md


def test_blocks_child_database():
    blocks = [
        {
            "type": "child_database",
            "child_database": {"title": "Sprint Board"},
            "children": [],
        }
    ]
    md = blocks_to_markdown(blocks)
    assert "Sprint Board" in md
    assert "database rows omitted" in md


def test_recursion_cap():
    """Blocks at exactly MAX_DEPTH+1 should be silently skipped."""
    # Build a chain of MAX_DEPTH + 2 nested paragraph blocks
    def make_chain(depth):
        block = {
            "type": "paragraph",
            "paragraph": {"rich_text": [_rt(f"depth-{depth}")]},
            "children": [],
        }
        if depth < MAX_DEPTH + 2:
            block["children"] = [make_chain(depth + 1)]
        return block

    root = [make_chain(0)]
    # Should not raise; deepest levels just get truncated
    md = blocks_to_markdown(root, depth=0)
    assert "depth-0" in md  # root is always present


def test_map_notion_page():
    item = {
        "id": "page-abc",
        "object": "page",
        "last_edited_time": "2024-01-01T00:00:00.000Z",
        "url": "https://notion.so/page-abc",
        "parent": {"type": "workspace"},
        "properties": {
            "title": {
                "type": "title",
                "title": [_rt("My Page")],
            }
        },
    }
    cf = map_notion_page(item)
    assert cf.external_id == "page-abc"
    assert cf.name == "My Page"
    assert cf.mime_type == "text/markdown"
    assert cf.external_path == "/workspace"
    assert cf.raw_metadata["object"] == "page"


def test_map_notion_database():
    item = {
        "id": "db-xyz",
        "object": "database",
        "last_edited_time": "2024-01-01T00:00:00.000Z",
        "url": "https://notion.so/db-xyz",
        "parent": {"type": "page_id", "page_id": "parent-1"},
        "title": [_rt("Sprint Tracker")],
        "properties": {},
    }
    cf = map_notion_page(item)
    assert cf.external_id == "db-xyz"
    assert cf.name == "Sprint Tracker"
    assert cf.external_path == "/pages/parent-1"


# ---------------------------------------------------------------------------
# Adapter unit tests
# ---------------------------------------------------------------------------

@pytest.fixture
def notion_adapter():
    return NotionAdapter()


@pytest.mark.asyncio
async def test_get_auth_url(notion_adapter):
    url = await notion_adapter.get_auth_url("state-42")
    assert "api.notion.com/v1/oauth/authorize" in url
    assert "state=state-42" in url
    assert "client_id" in url


@pytest.mark.asyncio
@patch("connectors.notion.adapter.exchange_code")
async def test_exchange_code(mock_exchange, notion_adapter):
    mock_exchange.return_value = (
        {
            "access_token": "secret_abc",
            "owner": {
                "user": {
                    "id": "user-1",
                    "person": {"email": "dev@example.com"},
                }
            },
        },
        datetime.now(timezone.utc),
    )
    data = await notion_adapter.exchange_code("code-xyz", "http://localhost")
    assert data["access_token"] == "secret_abc"
    assert data["provider_user_id"] == "user-1"
    assert data["provider_email"] == "dev@example.com"
