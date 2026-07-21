from connectors.registry import ConnectorRegistry
from .adapter import ConfluenceAdapter

try:
    ConnectorRegistry.register("confluence", ConfluenceAdapter)
except ValueError:
    pass
