# backend/app/governance/__init__.py
"""
Governance Layer - Cross-cutting concerns for AI Sandbox.

This module provides:
- RBAC (Role-Based Access Control) with permissions
- JWT authentication and authorization
- Immutable audit logging
- Secrets management integration
"""

from backend.app.governance.models import (
    AuditLog,
    AuditLogCreate,
    AuditLogRead,
    Permission,
    PermissionCreate,
    PermissionRead,
    Role,
    RoleCreate,
    RoleRead,
    RoleWithPermissions,
    User,
    UserCreate,
    UserRead,
    UserUpdate,
    UserWithRole,
)
from backend.app.governance.auth import (
    AuthService,
    get_current_user,
    get_current_active_user,
    require_permission,
)
from backend.app.governance.audit import AuditLogger
from backend.app.governance.secrets import (
    SecretsManager,
    get_secret,
    EnvironmentSecretsBackend,
    FileSecretsBackend,
    VaultSecretsBackend,
)

__all__ = [
    # Models
    "User",
    "Role",
    "Permission",
    "AuditLog",
    # Pydantic schemas
    "UserCreate",
    "UserRead",
    "UserUpdate",
    "UserWithRole",
    "RoleCreate",
    "RoleRead",
    "RoleWithPermissions",
    "PermissionCreate",
    "PermissionRead",
    "AuditLogCreate",
    "AuditLogRead",
    # Services
    "AuthService",
    "AuditLogger",
    "SecretsManager",
    # Dependencies
    "get_current_user",
    "get_current_active_user",
    "require_permission",
    # Convenience functions
    "get_secret",
    # Backends
    "EnvironmentSecretsBackend",
    "FileSecretsBackend",
    "VaultSecretsBackend",
]
