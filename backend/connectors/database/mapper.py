import os
from typing import Dict, Any, List

from connectors.base.metadata import ConnectorFileMetadata


def map_database_row(row_dict: Dict[str, Any], table_name: str, pk_col: str, mapping_config: Dict[str, Any]) -> ConnectorFileMetadata:
    """
    Map a database row to ConnectorFileMetadata.
    The actual document content will be rendered when download_file is called,
    or we can store the raw row data in raw_metadata for download_file to render.
    
    mapping_config expects:
    - title_template: optional, e.g., "Ticket {id}"
    - content_template: optional, e.g., "Description: {description}\nStatus: {status}"
    - content_columns: list of columns to include if content_template is not provided.
    """
    pk_val = str(row_dict.get(pk_col, ""))
    
    external_id = f"db://{table_name}/{pk_val}"
    
    # Render title if template is provided, else fallback to pk
    title_template = mapping_config.get("title_template")
    if title_template:
        try:
            name = title_template.format(**row_dict)
        except KeyError:
            name = f"{table_name}_{pk_val}"
    else:
        name = f"{table_name}_{pk_val}"
        
    # Append .md so that the ingestion pipeline knows it's markdown
    if not name.endswith(".md"):
        name += ".md"

    # We store the row data in raw_metadata so download_file can render it,
    # or we could render it now and store it. But download_file just returns bytes.
    # So we MUST store it so the adapter can use it, unless the adapter re-fetches.
    # Re-fetching by PK is an option, but storing row data is more efficient if it fits in metadata.
    # For now, we'll store it.
    
    return ConnectorFileMetadata(
        external_id=external_id,
        name=name,
        mime_type="text/markdown",
        size_bytes=0, # Will be computed at download time or roughly estimated
        external_path=external_id,
        raw_metadata={
            "provider": "database",
            "table_name": table_name,
            "pk_val": pk_val,
            "row_data": row_dict,
            "mapping_config": mapping_config,
        }
    )

def render_row_to_markdown(row_data: Dict[str, Any], mapping_config: Dict[str, Any]) -> str:
    """
    Render a database row to a Markdown document using the mapping config.
    """
    content_template = mapping_config.get("content_template")
    if content_template:
        try:
            return content_template.format(**row_data)
        except KeyError:
            # Fallback to key-value pairs if formatting fails
            pass
            
    content_columns = mapping_config.get("content_columns", list(row_data.keys()))
    
    lines = []
    for col in content_columns:
        val = row_data.get(col)
        lines.append(f"**{col}**: {val}")
        
    return "\n\n".join(lines)
