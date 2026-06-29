"""
services/tenant_registry.py

Manages tenant configuration, plan details, rate limits, and feature flags.
Answers "what is this tenant allowed to do".
"""

from typing import Dict, Optional
from pydantic import BaseModel, Field
from cachetools import TTLCache
from app.config import get_settings

class TenantConfig(BaseModel):
    tenant_id: str
    plan: str = Field(default="free")
    rate_limit_requests_per_minute: Optional[int] = Field(default=None)
    feature_overrides: Dict[str, bool] = Field(default_factory=dict)
    max_documents: Optional[int] = Field(default=None)
    storage_quota_bytes: Optional[int] = Field(default=None)


class TenantNotFoundError(Exception):
    def __init__(self, tenant_id: str):
        super().__init__(f"Tenant {tenant_id} not found")
        self.tenant_id = tenant_id


class TenantRegistry:
    def __init__(self):
        cfg = get_settings().tenancy
        # In-memory LRU cache with TTL
        self._cache = TTLCache(maxsize=1000, ttl=cfg.registry_cache_ttl_seconds)

    async def get_tenant_config(self, tenant_id: str) -> TenantConfig:
        """
        Fetch a tenant's configuration.
        """
        if tenant_id in self._cache:
            return self._cache[tenant_id]

        # For MVP, we'll return a default config for any valid tenant_id.
        # In a real system, this would query Postgres or a Redis hash.
        # For strict isolation testing, we assume any authenticated tenant is valid
        # and returns a basic config, or falls back to global settings.
        
        config = TenantConfig(tenant_id=tenant_id)
        
        # We can add actual DB lookups here when the Tenant table is integrated
        
        self._cache[tenant_id] = config
        return config

# Singleton instance
registry = TenantRegistry()
