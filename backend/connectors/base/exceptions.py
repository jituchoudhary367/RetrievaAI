class ConnectorError(Exception):
    """Base exception for all connector-related errors."""
    pass

class ConnectorAuthError(ConnectorError):
    """Raised when authentication fails (invalid credentials, expired tokens)."""
    pass

class ConnectorRateLimitError(ConnectorError):
    """Raised when the provider's API rate limits are exceeded."""
    pass

class ConnectorSyncError(ConnectorError):
    """Raised when an error occurs during synchronization."""
    pass

class ConnectorWebhookError(ConnectorError):
    """Raised when webhook registration or processing fails."""
    pass
