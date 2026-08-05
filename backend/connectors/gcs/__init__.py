from connectors.registry import ConnectorRegistry
from .adapter import GCSAdapter

try:
    ConnectorRegistry.register("gcs", GCSAdapter)
except ValueError:
    pass
