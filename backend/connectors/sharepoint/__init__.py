from connectors.registry import ConnectorRegistry
from .adapter import SharePointAdapter

try:
    ConnectorRegistry.register("sharepoint", SharePointAdapter)
except ValueError:
    pass
