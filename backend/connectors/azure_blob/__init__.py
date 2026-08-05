from connectors.registry import ConnectorRegistry
from .adapter import AzureBlobAdapter

try:
    ConnectorRegistry.register("azure_blob", AzureBlobAdapter)
except ValueError:
    pass
