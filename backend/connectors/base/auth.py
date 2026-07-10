from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseAuthProvider(ABC):
    """Base interface for connector authentication methods."""
    pass

class OAuth2AuthProvider(BaseAuthProvider):
    @abstractmethod
    async def get_auth_url(self, state: str) -> str:
        ...

    @abstractmethod
    async def exchange_code(self, auth_code: str, redirect_uri: str) -> Dict[str, Any]:
        ...

class APIKeyAuthProvider(BaseAuthProvider):
    pass

class ServiceAccountAuthProvider(BaseAuthProvider):
    pass
