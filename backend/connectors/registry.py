"""
connectors/registry.py

Connector registry — maps provider name strings to their connector classes.

Usage:
    from connectors.registry import ConnectorRegistry
    cls = ConnectorRegistry.get("google_drive")
    connector = cls()
"""

from __future__ import annotations

import logging
from typing import Dict, Type

from connectors.base import BaseConnector

logger = logging.getLogger(__name__)

_REGISTRY: Dict[str, Type[BaseConnector]] = {}


class ConnectorRegistry:
    """
    Central registry mapping provider names to connector classes.

    Providers register themselves by calling ConnectorRegistry.register()
    in their module, or it is called here at startup.
    """

    @classmethod
    def register(cls, provider_name: str, connector_class: Type[BaseConnector]) -> None:
        """Register a connector class under a provider name."""
        _REGISTRY[provider_name] = connector_class
        logger.debug("Registered connector: %s → %s", provider_name, connector_class.__name__)

    @classmethod
    def get(cls, provider_name: str) -> Type[BaseConnector]:
        """Return the connector class for the given provider name."""
        if provider_name not in _REGISTRY:
            available = list(_REGISTRY.keys())
            raise KeyError(
                f"Unknown connector provider: '{provider_name}'. "
                f"Available: {available}"
            )
        return _REGISTRY[provider_name]

    @classmethod
    def list_providers(cls) -> list[str]:
        """Return all registered provider names."""
        return list(_REGISTRY.keys())

    @classmethod
    def create(cls, provider_name: str) -> BaseConnector:
        """Instantiate and return a connector for the given provider."""
        connector_cls = cls.get(provider_name)
        return connector_cls()


def _register_builtin_connectors() -> None:
    """Register all built-in connectors. Called once at import time."""
    try:
        from connectors.google_drive.connector import GoogleDriveConnector
        ConnectorRegistry.register("google_drive", GoogleDriveConnector)
        logger.info("Google Drive connector registered.")
    except ImportError as exc:
        logger.warning("Google Drive connector unavailable (missing dependencies): %s", exc)
    except Exception as exc:
        logger.error("Failed to register Google Drive connector: %s", exc, exc_info=True)


# Register built-ins on import
_register_builtin_connectors()

__all__ = ["ConnectorRegistry"]
