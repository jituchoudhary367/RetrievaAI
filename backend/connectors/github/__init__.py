from connectors.registry import ConnectorRegistry
from .adapter import GithubAdapter

try:
    ConnectorRegistry.register("github", GithubAdapter)
except ValueError:
    pass
