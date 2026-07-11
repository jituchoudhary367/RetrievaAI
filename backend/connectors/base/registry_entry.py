from dataclasses import dataclass
from typing import Type
from .connector import BaseConnector
from .capabilities import CapabilitySet

@dataclass
class ConnectorRegistryEntry:
    """Metadata about a registered connector."""
    provider_name: str
    adapter_class: Type[BaseConnector]
    version: str
    capabilities: CapabilitySet
    enabled: bool = True
