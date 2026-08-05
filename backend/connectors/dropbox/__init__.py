from connectors.registry import ConnectorRegistry
from .adapter import DropboxAdapter

try:
    ConnectorRegistry.register("dropbox", DropboxAdapter)
except ValueError:
    pass
