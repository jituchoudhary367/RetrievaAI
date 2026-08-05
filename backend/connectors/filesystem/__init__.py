from connectors.registry import ConnectorRegistry
from .adapter import FilesystemAdapter

try:
    ConnectorRegistry.register("filesystem", FilesystemAdapter)
except ValueError:
    pass
