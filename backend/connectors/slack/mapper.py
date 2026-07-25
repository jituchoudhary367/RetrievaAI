from typing import Dict, Any, List
from datetime import datetime

from connectors.base.metadata import ConnectorFileMetadata

def map_slack_thread(thread_ts: str, channel_id: str, messages: List[Dict[str, Any]]) -> ConnectorFileMetadata:
    """
    Map a Slack thread (list of messages) to a single Markdown ConnectorFileMetadata payload.
    """
    if not messages:
        return ConnectorFileMetadata(
            external_id=thread_ts,
            name=f"Thread {thread_ts}",
            mime_type="text/markdown",
            size_bytes=0,
            external_path=f"/channels/{channel_id}",
            raw_metadata={"channel_id": channel_id, "thread_ts": thread_ts}
        )

    # The first message in the thread is the parent
    parent_msg = messages[0]
    
    # Try to extract a title from the parent message
    text = parent_msg.get("text", "")
    title_line = text.split('\n')[0][:50]
    title = title_line if title_line else f"Thread {thread_ts}"
    
    # Create markdown content
    md_lines = [f"# {title}", ""]
    
    for msg in messages:
        user = msg.get("user") or msg.get("username", "Unknown")
        ts_float = float(msg.get("ts", 0))
        time_str = datetime.fromtimestamp(ts_float).strftime('%Y-%m-%d %H:%M:%S')
        
        md_lines.append(f"**{user}** at {time_str}:")
        md_lines.append(msg.get("text", ""))
        
        files = msg.get("files", [])
        if files:
            md_lines.append("\n*Attachments:*")
            for f in files:
                md_lines.append(f"- {f.get('name', 'file')} ({f.get('url_private', '')})")
                
        md_lines.append("\n---\n")

    md_content = "\n".join(md_lines)
    
    return ConnectorFileMetadata(
        external_id=thread_ts,
        name=title,
        mime_type="text/markdown",
        size_bytes=len(md_content.encode('utf-8')),
        external_path=f"/channels/{channel_id}",
        raw_metadata={
            "channel_id": channel_id,
            "thread_ts": thread_ts,
            "type": "thread_document",
            "markdown_content": md_content # Temporary stash for the adapter to retrieve
        }
    )

def map_slack_attachment(file_obj: Dict[str, Any], channel_id: str, thread_ts: str) -> ConnectorFileMetadata:
    """
    Map a Slack file attachment to ConnectorFileMetadata.
    """
    file_id = file_obj.get("id", "")
    name = file_obj.get("name", "Untitled")
    mime_type = file_obj.get("mimetype", "application/octet-stream")
    size = file_obj.get("size", 0)
    
    return ConnectorFileMetadata(
        external_id=f"file_{file_id}",
        name=name,
        mime_type=mime_type,
        size_bytes=size,
        external_path=f"/channels/{channel_id}/{thread_ts}",
        raw_metadata={
            "channel_id": channel_id,
            "thread_ts": thread_ts,
            "file_id": file_id,
            "url_private": file_obj.get("url_private", ""),
            "type": "attachment"
        }
    )
