# backend/app/governance/models.py
"""
SQLAlchemy models and Pydantic schemas for governance (Users, Roles, Permissions, Audit).
"""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import DateTime, ForeignKey, String, Table, Column, Text, Boolean, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base, TimestampMixin


# ============================================================================
# Enums
# ============================================================================


class PermissionAction(str, Enum):
    """Standard CRUD + execute actions."""

    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"


class ResourceType(str, Enum):
    """Resources that can be protected by RBAC."""

    DATASET = "dataset"
    EXPERIMENT = "experiment"
    MODEL = "model"
    EVALUATION = "evaluation"
    REPORT = "report"
    USER = "user"
    ROLE = "role"
    AUDIT_LOG = "audit_log"
    SYSTEM = "system"


class AuditAction(str, Enum):
    """Actions that can be audited."""

    LOGIN = "login"
    LOGOUT = "logout"
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"
    EXPORT = "export"
    IMPORT = "import"
    FAILED_LOGIN = "failed_login"
    PERMISSION_DENIED = "permission_denied"


# ============================================================================
# Association Tables
# ============================================================================

role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", PGUUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", PGUUID(as_uuid=True), ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
)


# ============================================================================
# SQLAlchemy Models
# ============================================================================


class Permission(Base):
    """Permission model - defines what actions are allowed on which resources."""

    __tablename__ = "permissions"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    resource: Mapped[str] = mapped_column(String(50), nullable=False)  # ResourceType value
    action: Mapped[str] = mapped_column(String(20), nullable=False)  # PermissionAction value

    # Relationships
    roles: Mapped[list["Role"]] = relationship(
        secondary=role_permissions,
        back_populates="permissions",
    )

    def __repr__(self) -> str:
        return f"<Permission {self.name}>"


class Role(Base, TimestampMixin):
    """Role model - groups permissions together."""

    __tablename__ = "roles"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    permissions: Mapped[list[Permission]] = relationship(
        secondary=role_permissions,
        back_populates="roles",
        lazy="selectin",
    )
    users: Mapped[list["User"]] = relationship(back_populates="role")

    def __repr__(self) -> str:
        return f"<Role {self.name}>"

    def has_permission(self, resource: str, action: str) -> bool:
        """Check if this role has the specified permission."""
        for perm in self.permissions:
            if perm.resource == resource and perm.action == action:
                return True
            # Wildcard: system:* grants all permissions
            if perm.resource == "system" and perm.action == "execute":
                return True
        return False


class User(Base, TimestampMixin):
    """User model with role-based access control."""

    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Foreign keys
    role_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    role: Mapped[Role | None] = relationship(back_populates="users", lazy="selectin")

    def __repr__(self) -> str:
        return f"<User {self.username}>"

    def has_permission(self, resource: str, action: str) -> bool:
        """Check if user has permission (via role or superuser status)."""
        if self.is_superuser:
            return True
        if self.role:
            return self.role.has_permission(resource, action)
        return False


class AuditLog(Base):
    """Immutable audit log entry - records all sensitive operations."""

    __tablename__ = "audit_logs"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # Who
    user_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True, index=True)
    username: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)  # IPv6 max length

    # What
    action: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # AuditAction value
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # ResourceType value
    resource_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)

    # Details
    details: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="success", nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Correlation
    request_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    session_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    def __repr__(self) -> str:
        return f"<AuditLog {self.action} on {self.resource_type}:{self.resource_id}>"


# ============================================================================
# Pydantic Schemas
# ============================================================================


class PermissionCreate(BaseModel):
    """Schema for creating a permission."""

    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    resource: ResourceType
    action: PermissionAction


class PermissionRead(BaseModel):
    """Schema for reading a permission."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None
    resource: str
    action: str


class RoleCreate(BaseModel):
    """Schema for creating a role."""

    name: str = Field(..., min_length=1, max_length=50)
    description: str | None = None
    permission_ids: list[UUID] = Field(default_factory=list)


class RoleRead(BaseModel):
    """Schema for reading a role."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None
    is_system: bool
    created_at: datetime
    updated_at: datetime


class RoleWithPermissions(RoleRead):
    """Schema for reading a role with its permissions."""

    permissions: list[PermissionRead]


class UserCreate(BaseModel):
    """Schema for creating a user."""

    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=8)
    full_name: str | None = None
    role_id: UUID | None = None


class UserRead(BaseModel):
    """Schema for reading a user."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    username: str
    full_name: str | None
    is_active: bool
    is_superuser: bool
    role_id: UUID | None
    created_at: datetime
    updated_at: datetime


class UserWithRole(UserRead):
    """Schema for reading a user with role details."""

    role: RoleRead | None


class UserUpdate(BaseModel):
    """Schema for updating a user."""

    email: EmailStr | None = None
    username: str | None = Field(default=None, min_length=3, max_length=100)
    full_name: str | None = None
    is_active: bool | None = None
    role_id: UUID | None = None


class AuditLogCreate(BaseModel):
    """Schema for creating an audit log entry."""

    user_id: UUID | None = None
    username: str | None = None
    ip_address: str | None = None
    action: AuditAction
    resource_type: ResourceType
    resource_id: str | None = None
    details: dict[str, Any] | None = None
    status: str = "success"
    error_message: str | None = None
    request_id: str | None = None
    session_id: str | None = None


class AuditLogRead(BaseModel):
    """Schema for reading an audit log entry."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    timestamp: datetime
    user_id: UUID | None
    username: str | None
    ip_address: str | None
    action: str
    resource_type: str
    resource_id: str | None
    details: dict[str, Any] | None
    status: str
    error_message: str | None
    request_id: str | None


# ============================================================================
# Token Schemas
# ============================================================================


class Token(BaseModel):
    """JWT token response."""

    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """JWT token payload."""

    sub: str  # user_id
    username: str
    email: str
    is_superuser: bool = False
    permissions: list[str] = Field(default_factory=list)
    exp: datetime | None = None
