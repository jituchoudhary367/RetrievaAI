from typing import Dict, Any

from connectors.base.metadata import ConnectorFileMetadata

def map_sharepoint_item(item: Dict[str, Any], site_id: str, list_id: str) -> ConnectorFileMetadata:
    """
    Map a Microsoft Graph DriveItem from SharePoint to a ConnectorFileMetadata payload.
    """
    file_id = item.get('id', '')
    name = item.get('name', 'Untitled')
    mime_type = item.get('file', {}).get('mimeType', '')
    
    if 'folder' in item:
        mime_type = 'application/vnd.microsoft.graph.folder'
        
    size_bytes = item.get('size', 0)
    
    # external_path represents the site/library hierarchy if available
    # The parentReference usually has the path
    external_path = None
    parent_ref = item.get('parentReference', {})
    if 'path' in parent_ref:
        # e.g., /drive/root:/FolderName
        external_path = parent_ref['path']

    return ConnectorFileMetadata(
        external_id=file_id,
        name=name,
        mime_type=mime_type,
        size_bytes=size_bytes,
        external_path=external_path,
        raw_metadata={
            **item,
            "siteId": site_id,
            "listId": list_id
        }
    )
