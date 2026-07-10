from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseWebhookHandler(ABC):
    """
    Interface for handling incoming webhook events from a provider.
    """
    @abstractmethod
    async def process_payload(self, request_headers: Dict[str, str], raw_body: bytes) -> Dict[str, Any]:
        """
        Validates signature, parses payload, and returns standardized event dict.
        """
        ...
