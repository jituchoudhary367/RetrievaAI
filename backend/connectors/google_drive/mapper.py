from typing import Dict, Any, List
from connectors.base.metadata import ConnectorFileMetadata, ConnectorPermission

def map_drive_file_to_metadata(item: Dict[str, Any]) -> ConnectorFileMetadata:
    """
    Map a raw Google Drive API file resource into the standardized ConnectorFileMetadata.
    """
    permissions = []
    
    # Optional: If permissions were requested and returned in the item
    raw_perms = item.get("permissions", [])
    for p in raw_perms:
        principal_type = "user" # default
        if p.get("type") == "group":
            principal_type = "group"
        elif p.get("type") == "domain":
            principal_type = "domain"
        elif p.get("type") == "anyone":
            principal_type = "anyone"
            
        permissions.append(ConnectorPermission(
            principal_type=principal_type,
            principal_id=p.get("emailAddress", p.get("domain", p.get("id", ""))),
            role=p.get("role", "reader")
        ))
        
    return ConnectorFileMetadata(
        external_id=item["id"],
        external_path="/".join(item.get("parents", [])), # Simplified path, actual hierarchy needs recursive fetch
        name=item.get("name", ""),
        mime_type=item.get("mimeType", ""),
        size_bytes=int(item.get("size", 0)) if "size" in item else None,
        raw_metadata={
            "modifiedTime": item.get("modifiedTime"),
            "createdTime": item.get("createdTime"),
            "webViewLink": item.get("webViewLink"),
            "trashed": item.get("trashed", False)
        },
        permissions=permissions
    )
