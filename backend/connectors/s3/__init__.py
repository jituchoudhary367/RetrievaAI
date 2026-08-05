from connectors.registry import ConnectorRegistry
from .adapter import S3Adapter

try:
    ConnectorRegistry.register("s3", S3Adapter)
except ValueError:
    pass
