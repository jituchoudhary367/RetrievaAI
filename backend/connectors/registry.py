import importlib
import logging
import pkgutil
import inspect
from typing import Dict, Type, List, Optional
import sys
import os

from connectors.base.connector import BaseConnector
from connectors.base.registry_entry import ConnectorRegistryEntry
from connectors.base.capabilities import CapabilitySet

logger = logging.getLogger(__name__)

class ConnectorRegistry:
    """
    Central, capability-aware registry for all data connectors.
    Connectors are dynamically discovered at startup.
    """
    _entries: Dict[str, ConnectorRegistryEntry] = {}

    @classmethod
    def register(cls, provider_name: str, connector_class: Type[BaseConnector], version: str = "1.0.0") -> None:
        if provider_name in cls._entries:
            raise ValueError(f"Connector '{provider_name}' is already registered.")

        # Instantiate briefly to get capabilities
        try:
            temp_instance = connector_class()
            capabilities = temp_instance.capabilities()
        except Exception as e:
            logger.error(f"Failed to extract capabilities from {provider_name}: {e}")
            capabilities = set()

        entry = ConnectorRegistryEntry(
            provider_name=provider_name,
            adapter_class=connector_class,
            version=version,
            capabilities=capabilities,
            enabled=True
        )
        # We attach the schema directly to the entry class for easy retrieval
        entry.schema = connector_class.get_credentials_schema()
        cls._entries[provider_name] = entry
        logger.debug(f"Registered connector: {provider_name} v{version} ({len(capabilities)} capabilities)")

    @classmethod
    def get(cls, provider_name: str) -> Type[BaseConnector]:
        if provider_name not in cls._entries:
            raise KeyError(f"Unknown connector provider: '{provider_name}'")
        return cls._entries[provider_name].adapter_class

    @classmethod
    def enable(cls, provider_name: str) -> None:
        if provider_name not in cls._entries:
            raise KeyError(f"Unknown connector provider: '{provider_name}'")
        cls._entries[provider_name].enabled = True
        logger.info(f"Enabled connector: {provider_name}")

    @classmethod
    def disable(cls, provider_name: str) -> None:
        """
        Disables the connector. Stops new task dispatch but does not cancel
        already-queued tasks; cleanup of orphaned tasks is handled downstream.
        """
        if provider_name not in cls._entries:
            raise KeyError(f"Unknown connector provider: '{provider_name}'")
        cls._entries[provider_name].enabled = False
        logger.info(f"Disabled connector: {provider_name}")

    @classmethod
    def list_active(cls) -> List[str]:
        return [name for name, entry in cls._entries.items() if entry.enabled]
        
    @classmethod
    def get_schemas(cls) -> Dict[str, list[dict]]:
        """Return the credential schemas for all active connectors."""
        return {
            name: getattr(entry, "schema", []) 
            for name, entry in cls._entries.items() if entry.enabled
        }
        
    @classmethod
    def get_entry(cls, provider_name: str) -> ConnectorRegistryEntry:
        if provider_name not in cls._entries:
            raise KeyError(f"Unknown connector provider: '{provider_name}'")
        return cls._entries[provider_name]

    @classmethod
    def capabilities_of(cls, provider_name: str) -> CapabilitySet:
        if provider_name not in cls._entries:
            raise KeyError(f"Unknown connector provider: '{provider_name}'")
        return cls._entries[provider_name].capabilities

    @classmethod
    def clear(cls) -> None:
        """For testing purposes."""
        cls._entries.clear()

    @classmethod
    def autodiscover(cls) -> None:
        """
        Scan all subdirectories of `connectors` for `adapter.py`, import them,
        and register any BaseConnector implementations found.
        """
        connectors_dir = os.path.dirname(os.path.abspath(__file__))
        for folder_name in os.listdir(connectors_dir):
            adapter_path = os.path.join(connectors_dir, folder_name, "adapter.py")
            if os.path.isfile(adapter_path):
                module_name = f"connectors.{folder_name}.adapter"
                try:
                    module = importlib.import_module(module_name)
                    
                    # Find BaseConnector subclasses in this module
                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        if issubclass(obj, BaseConnector) and obj is not BaseConnector:
                            version = getattr(module, "ADAPTER_VERSION", "1.0.0")
                            try:
                                cls.register(
                                    provider_name=folder_name, 
                                    connector_class=obj, 
                                    version=version
                                )
                            except ValueError as e:
                                logger.debug(f"Autodiscover skip: {e}")
                except Exception as e:
                    logger.error(f"Failed to load connector from {module_name}: {e}")

# Trigger autodiscover on import
ConnectorRegistry.autodiscover()
