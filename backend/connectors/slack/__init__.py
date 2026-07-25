from connectors.registry import ConnectorRegistry
from .adapter import SlackAdapter

try:
    ConnectorRegistry.register("slack", SlackAdapter)
except ValueError:
    pass
