from connectors.registry import ConnectorRegistry
from .adapter import OneDriveAdapter

# Register the OneDrive adapter
try:
    ConnectorRegistry.register("onedrive", OneDriveAdapter)
except ValueError:
    pass
