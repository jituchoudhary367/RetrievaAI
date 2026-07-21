from connectors.registry import ConnectorRegistry
from .adapter import NotionAdapter

try:
    ConnectorRegistry.register("notion", NotionAdapter)
except ValueError:
    pass
