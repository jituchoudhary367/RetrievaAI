from enum import Enum
from typing import Set

class Capability(str, Enum):
    OAUTH = "oauth"
    API_KEY_AUTH = "api_key_auth"
    WEBHOOKS = "webhooks"
    INCREMENTAL_SYNC = "incremental_sync"
    SCHEDULED_SYNC = "scheduled_sync"
    FOLDER_SYNC = "folder_sync"
    DELETE_EVENTS = "delete_events"
    ACL_SYNC = "acl_sync"
    METADATA_EXTRACTION = "metadata_extraction"
    BINARY_FILE_SUPPORT = "binary_file_support"
    NATIVE_SEARCH = "native_search"
    DELTA_API = "delta_api"
    CHANGE_NOTIFICATIONS = "change_notifications"

CapabilitySet = Set[Capability]
