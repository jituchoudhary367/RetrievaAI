from typing import Dict, Any

from connectors.base.metadata import ConnectorFileMetadata

def map_onedrive_item(item: Dict[str, Any]) -> ConnectorFileMetadata:
    """
    Map a Microsoft Graph DriveItem to a ConnectorFileMetadata payload.
    """
    file_id = item.get('id', '')
    name = item.get('name', 'Untitled')
    mime_type = item.get('file', {}).get('mimeType', '')
    
    if 'folder' in item:
        mime_type = 'application/vnd.microsoft.graph.folder'
        
    size_bytes = item.get('size', 0)

    return ConnectorFileMetadata(
        external_id=file_id,
        name=name,
        mime_type=mime_type,
        size_bytes=size_bytes,
        raw_metadata=item
    )
