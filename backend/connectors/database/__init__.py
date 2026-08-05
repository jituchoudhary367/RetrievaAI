from connectors.registry import ConnectorRegistry
from .adapter import DatabaseAdapter

try:
    ConnectorRegistry.register("database", DatabaseAdapter)
except ValueError:
    pass
