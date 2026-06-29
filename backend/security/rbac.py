"""
security/rbac.py

Role-Based Access Control (RBAC) definitions and dependencies.
Builds on top of `TenantContext.roles` extracted from the JWT.
"""

import logging
from enum import Enum
from typing import Set

from fastapi import Depends, HTTPException, status
from fastapi.requests import Request

from app.models import TenantContext
from security.auth import get_tenant_context

logger = logging.getLogger(__name__)


class AuthorizationError(HTTPException):
    def __init__(self, detail: str = "Not permitted"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )


class Role(str, Enum):
    VIEWER = "viewer"
    MEMBER = "member"
    ADMIN = "admin"
    PLATFORM_ADMIN = "platform_admin"


class Permission(str, Enum):
    SEARCH_READ = "search:read"
    QUERY_WRITE = "query:write"
    TENANT_ADMIN = "tenant:admin"


# The definitive matrix of what roles grant which permissions.
ROLE_PERMISSIONS: dict[Role, set[Permission]] = {
    Role.VIEWER: {Permission.SEARCH_READ},
    Role.MEMBER: {Permission.SEARCH_READ, Permission.QUERY_WRITE},
    Role.ADMIN: {Permission.SEARCH_READ, Permission.QUERY_WRITE, Permission.TENANT_ADMIN},
    Role.PLATFORM_ADMIN: set(),  # Reserved for future cross-tenant ops
}


def parse_roles(raw_roles: list[str]) -> set[Role]:
    """
    Convert raw string roles to `Role` enums, dropping unrecognized strings.
    """
    parsed: set[Role] = set()
    for raw in raw_roles:
        try:
            parsed.add(Role(raw))
        except ValueError:
            logger.warning(f"Unrecognized role string found in token: {raw}")
    return parsed


def require_permission(permission: Permission):
    """
    FastAPI dependency factory to enforce RBAC.
    Depends on `get_tenant_context` to read the caller's JWT roles.
    Raises AuthorizationError (403) if the required permission is not present.
    """
    async def _check_permission(
        request: Request,
        tenant_context: TenantContext = Depends(get_tenant_context),
    ) -> TenantContext:
        roles = parse_roles(tenant_context.roles)
        
        # Aggregate all granted permissions across the user's valid roles
        granted_permissions: set[Permission] = set()
        for role in roles:
            granted_permissions.update(ROLE_PERMISSIONS.get(role, set()))
            
        if permission not in granted_permissions:
            raise AuthorizationError(f"Requires permission: {permission.value}")
            
        return tenant_context
        
    return _check_permission
