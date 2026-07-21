import logging
from typing import Dict, Any, List, Optional

from connectors.base.metadata import ConnectorFileMetadata

logger = logging.getLogger(__name__)

MAX_DEPTH = 10  # cap recursion depth to prevent runaway API calls


# ---------------------------------------------------------------------------
# Block-tree → Markdown
# ---------------------------------------------------------------------------

def _rich_text_to_str(rich_text: List[Dict[str, Any]]) -> str:
    """Flatten a Notion rich_text array to plain text."""
    parts = []
    for rt in rich_text:
        text = rt.get("plain_text", "")
        annotations = rt.get("annotations", {})
        if annotations.get("bold"):
            text = f"**{text}**"
        if annotations.get("italic"):
            text = f"*{text}*"
        if annotations.get("code"):
            text = f"`{text}`"
        if annotations.get("strikethrough"):
            text = f"~~{text}~~"
        if rt.get("href"):
            text = f"[{text}]({rt['href']})"
        parts.append(text)
    return "".join(parts)


def blocks_to_markdown(blocks: List[Dict[str, Any]], depth: int = 0) -> str:
    """
    Recursively convert a list of Notion block objects to Markdown.
    Caps recursion at MAX_DEPTH.
    """
    if depth > MAX_DEPTH:
        logger.warning("Notion block recursion depth exceeded MAX_DEPTH=%d — truncating", MAX_DEPTH)
        return ""

    lines: List[str] = []
    indent = "  " * depth

    for block in blocks:
        block_type = block.get("type", "")
        content = block.get(block_type, {})
        children = block.get("children", [])  # pre-fetched children

        if block_type == "paragraph":
            text = _rich_text_to_str(content.get("rich_text", []))
            lines.append(f"{indent}{text}\n")

        elif block_type in ("heading_1", "heading_2", "heading_3"):
            level = {"heading_1": 1, "heading_2": 2, "heading_3": 3}[block_type]
            text = _rich_text_to_str(content.get("rich_text", []))
            lines.append(f"\n{'#' * level} {text}\n")

        elif block_type == "bulleted_list_item":
            text = _rich_text_to_str(content.get("rich_text", []))
            lines.append(f"{indent}- {text}")
            if children:
                lines.append(blocks_to_markdown(children, depth + 1))

        elif block_type == "numbered_list_item":
            text = _rich_text_to_str(content.get("rich_text", []))
            lines.append(f"{indent}1. {text}")
            if children:
                lines.append(blocks_to_markdown(children, depth + 1))

        elif block_type == "toggle":
            text = _rich_text_to_str(content.get("rich_text", []))
            lines.append(f"{indent}**{text}**")  # treat toggle header as bold
            if children:
                lines.append(blocks_to_markdown(children, depth + 1))

        elif block_type == "code":
            language = content.get("language", "")
            code_text = _rich_text_to_str(content.get("rich_text", []))
            lines.append(f"\n```{language}\n{code_text}\n```\n")

        elif block_type == "quote":
            text = _rich_text_to_str(content.get("rich_text", []))
            lines.append(f"{indent}> {text}")

        elif block_type == "divider":
            lines.append("\n---\n")

        elif block_type == "child_database":
            title = content.get("title", "Database")
            lines.append(f"\n**[Database: {title}]**\n")
            # Skip row enumeration for now — mark as truncated
            lines.append(f"{indent}*(database rows omitted)*\n")

        elif block_type == "to_do":
            checked = content.get("checked", False)
            text = _rich_text_to_str(content.get("rich_text", []))
            checkbox = "x" if checked else " "
            lines.append(f"{indent}- [{checkbox}] {text}")

        elif block_type == "callout":
            icon = content.get("icon", {}).get("emoji", "📌")
            text = _rich_text_to_str(content.get("rich_text", []))
            lines.append(f"{indent}> {icon} {text}")

        elif block_type in ("image", "video", "file", "pdf"):
            external = content.get("external", {}).get("url", "")
            file_url = content.get("file", {}).get("url", "") or external
            caption = _rich_text_to_str(content.get("caption", []))
            lines.append(f"\n![{caption or block_type}]({file_url})\n")

        else:
            # Unknown block type — log and skip
            logger.debug("Skipping unsupported Notion block type: %s", block_type)

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Page → ConnectorFileMetadata
# ---------------------------------------------------------------------------

def map_notion_page(item: Dict[str, Any]) -> ConnectorFileMetadata:
    """Map a Notion Page or Database object to ConnectorFileMetadata."""
    page_id = item.get("id", "")
    object_type = item.get("object", "page")  # "page" or "database"

    # Notion stores the title differently for pages vs databases
    title = "Untitled"
    properties = item.get("properties", {})

    if object_type == "database":
        title_parts = item.get("title", [])
        title = _rich_text_to_str(title_parts) or "Untitled Database"
    else:
        # Pages have a "title" property (or "Name" in databases)
        for prop_name, prop_val in properties.items():
            if prop_val.get("type") == "title":
                title = _rich_text_to_str(prop_val.get("title", []))
                break

    parent = item.get("parent", {})
    if parent.get("type") == "workspace":
        external_path = "/workspace"
    elif parent.get("type") == "page_id":
        external_path = f"/pages/{parent.get('page_id', '')}"
    elif parent.get("type") == "database_id":
        external_path = f"/databases/{parent.get('database_id', '')}"
    else:
        external_path = "/"

    last_edited = item.get("last_edited_time", "")

    return ConnectorFileMetadata(
        external_id=page_id,
        name=title,
        mime_type="text/markdown",
        size_bytes=0,
        external_path=external_path,
        raw_metadata={
            "object": object_type,
            "last_edited_time": last_edited,
            "url": item.get("url", ""),
        },
    )
