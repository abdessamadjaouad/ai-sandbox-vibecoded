# backend/app/api/auth/routes.py
"""
Authentication and user management API routes.

Provides:
- User registration and login
- Token refresh
- User CRUD operations
- Role and permission management
- Audit log queries
"""

from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db_session
from backend.app.core.logging import get_logger
from backend.app.governance.audit import AuditLogger
from backend.app.governance.auth import (
    AuthService,
    RequiredUser,
    get_current_active_user,
    require_permission,
)
from backend.app.governance.models import (
    AuditAction,
    AuditLogRead,
    Permission,
    PermissionCreate,
    PermissionRead,
    ResourceType,
    Role,
    RoleCreate,
    RoleRead,
    RoleWithPermissions,
    Token,
    User,
    UserCreate,
    UserRead,
    UserUpdate,
    UserWithRole,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["authentication"])


def _get_client_ip(request: Request) -> str | None:
    """Extract client IP from request headers."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


# ============================================================================
# Authentication Endpoints
# ============================================================================


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> User:
    """
    Register a new user.

    The first user registered becomes a superuser automatically.
    """
    # Check if email or username already exists
    existing = await db.execute(
        select(User).where((User.email == user_data.email) | (User.username == user_data.username))
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or username already registered",
        )

    # Check if this is the first user (make them superuser)
    count_result = await db.execute(select(func.count(User.id)))
    user_count = count_result.scalar() or 0
    is_first_user = user_count == 0

    # Create user
    user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=AuthService.hash_password(user_data.password),
        full_name=user_data.full_name,
        role_id=user_data.role_id,
        is_superuser=is_first_user,
    )
    db.add(user)
    await db.flush()

    # Audit log
    audit = AuditLogger(db)
    await audit.log(
        action=AuditAction.CREATE,
        resource_type=ResourceType.USER,
        resource_id=str(user.id),
        user=user,
        ip_address=_get_client_ip(request),
        details={"username": user.username, "email": user.email, "is_first_user": is_first_user},
    )

    logger.info("user_registered", user_id=str(user.id), username=user.username)
    return user


@router.post("/login", response_model=Token)
async def login(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> Token:
    """
    Authenticate user and return JWT token.

    Accepts username or email in the username field.
    """
    user = await AuthService.authenticate_user(db, form_data.username, form_data.password)

    audit = AuditLogger(db)

    if not user:
        # Log failed login attempt (we don't have user, so minimal info)
        await audit.log(
            action=AuditAction.FAILED_LOGIN,
            resource_type=ResourceType.USER,
            ip_address=_get_client_ip(request),
            status="failure",
            details={"attempted_username": form_data.username},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Log successful login
    await audit.log_login(user, ip_address=_get_client_ip(request), success=True)

    return AuthService.create_access_token(user)


@router.post("/logout")
async def logout(
    request: Request,
    current_user: RequiredUser,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict[str, str]:
    """
    Logout current user.

    Note: With JWT tokens, this mainly logs the logout event.
    Client should discard the token.
    """
    audit = AuditLogger(db)
    await audit.log_logout(current_user, ip_address=_get_client_ip(request))

    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserWithRole)
async def get_current_user_info(
    current_user: RequiredUser,
) -> User:
    """Get current authenticated user's information."""
    return current_user


@router.put("/me", response_model=UserRead)
async def update_current_user(
    user_data: UserUpdate,
    request: Request,
    current_user: RequiredUser,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> User:
    """Update current authenticated user's information."""
    update_fields = user_data.model_dump(exclude_unset=True)

    # Users cannot change their own role or active status
    update_fields.pop("role_id", None)
    update_fields.pop("is_active", None)

    if not update_fields:
        return current_user

    # Check for duplicate email/username
    if "email" in update_fields:
        existing = await db.execute(
            select(User).where(User.email == update_fields["email"], User.id != current_user.id)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Email already in use")

    if "username" in update_fields:
        existing = await db.execute(
            select(User).where(User.username == update_fields["username"], User.id != current_user.id)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Username already in use")

    for field, value in update_fields.items():
        setattr(current_user, field, value)

    # Audit log
    audit = AuditLogger(db)
    await audit.log(
        action=AuditAction.UPDATE,
        resource_type=ResourceType.USER,
        resource_id=str(current_user.id),
        user=current_user,
        ip_address=_get_client_ip(request),
        details={"updated_fields": list(update_fields.keys())},
    )

    return current_user


# ============================================================================
# User Management (Admin)
# ============================================================================


@router.get(
    "/users",
    response_model=list[UserRead],
    dependencies=[Depends(require_permission("user", "read"))],
)
async def list_users(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> list[User]:
    """List all users (requires user:read permission)."""
    result = await db.execute(select(User).order_by(User.created_at.desc()).offset(skip).limit(limit))
    return list(result.scalars().all())


@router.get(
    "/users/{user_id}",
    response_model=UserWithRole,
    dependencies=[Depends(require_permission("user", "read"))],
)
async def get_user(
    user_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> User:
    """Get a specific user by ID (requires user:read permission)."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put(
    "/users/{user_id}",
    response_model=UserRead,
    dependencies=[Depends(require_permission("user", "update"))],
)
async def update_user(
    user_id: UUID,
    user_data: UserUpdate,
    request: Request,
    current_user: RequiredUser,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> User:
    """Update a user (requires user:update permission)."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Cannot modify superuser status or deactivate yourself
    if user.id == current_user.id and user_data.is_active is False:
        raise HTTPException(status_code=400, detail="Cannot deactivate your own account")

    update_fields = user_data.model_dump(exclude_unset=True)
    for field, value in update_fields.items():
        setattr(user, field, value)

    # Audit log
    audit = AuditLogger(db)
    await audit.log(
        action=AuditAction.UPDATE,
        resource_type=ResourceType.USER,
        resource_id=str(user.id),
        user=current_user,
        ip_address=_get_client_ip(request),
        details={"target_user": user.username, "updated_fields": list(update_fields.keys())},
    )

    return user


@router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("user", "delete"))],
)
async def delete_user(
    user_id: UUID,
    request: Request,
    current_user: RequiredUser,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> None:
    """Delete a user (requires user:delete permission)."""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.is_superuser:
        raise HTTPException(status_code=400, detail="Cannot delete superuser account")

    username = user.username
    await db.delete(user)

    # Audit log
    audit = AuditLogger(db)
    await audit.log(
        action=AuditAction.DELETE,
        resource_type=ResourceType.USER,
        resource_id=str(user_id),
        user=current_user,
        ip_address=_get_client_ip(request),
        details={"deleted_user": username},
    )


# ============================================================================
# Role Management
# ============================================================================


@router.get(
    "/roles",
    response_model=list[RoleWithPermissions],
    dependencies=[Depends(require_permission("role", "read"))],
)
async def list_roles(
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[Role]:
    """List all roles with their permissions (requires role:read permission)."""
    result = await db.execute(select(Role).order_by(Role.name))
    return list(result.scalars().all())


@router.post(
    "/roles",
    response_model=RoleRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("role", "create"))],
)
async def create_role(
    role_data: RoleCreate,
    request: Request,
    current_user: RequiredUser,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> Role:
    """Create a new role (requires role:create permission)."""
    # Check for duplicate name
    existing = await db.execute(select(Role).where(Role.name == role_data.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Role name already exists")

    # Get permissions
    permissions = []
    if role_data.permission_ids:
        result = await db.execute(select(Permission).where(Permission.id.in_(role_data.permission_ids)))
        permissions = list(result.scalars().all())

    role = Role(
        name=role_data.name,
        description=role_data.description,
        permissions=permissions,
    )
    db.add(role)
    await db.flush()

    # Audit log
    audit = AuditLogger(db)
    await audit.log(
        action=AuditAction.CREATE,
        resource_type=ResourceType.ROLE,
        resource_id=str(role.id),
        user=current_user,
        ip_address=_get_client_ip(request),
        details={"role_name": role.name, "permission_count": len(permissions)},
    )

    return role


@router.delete(
    "/roles/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("role", "delete"))],
)
async def delete_role(
    role_id: UUID,
    request: Request,
    current_user: RequiredUser,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> None:
    """Delete a role (requires role:delete permission)."""
    result = await db.execute(select(Role).where(Role.id == role_id))
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    if role.is_system:
        raise HTTPException(status_code=400, detail="Cannot delete system role")

    role_name = role.name
    await db.delete(role)

    # Audit log
    audit = AuditLogger(db)
    await audit.log(
        action=AuditAction.DELETE,
        resource_type=ResourceType.ROLE,
        resource_id=str(role_id),
        user=current_user,
        ip_address=_get_client_ip(request),
        details={"deleted_role": role_name},
    )


# ============================================================================
# Permission Management
# ============================================================================


@router.get(
    "/permissions",
    response_model=list[PermissionRead],
    dependencies=[Depends(require_permission("role", "read"))],
)
async def list_permissions(
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[Permission]:
    """List all available permissions (requires role:read permission)."""
    result = await db.execute(select(Permission).order_by(Permission.resource, Permission.action))
    return list(result.scalars().all())


@router.post(
    "/permissions",
    response_model=PermissionRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("role", "create"))],
)
async def create_permission(
    perm_data: PermissionCreate,
    request: Request,
    current_user: RequiredUser,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> Permission:
    """Create a new permission (requires role:create permission)."""
    # Check for duplicate
    existing = await db.execute(select(Permission).where(Permission.name == perm_data.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Permission name already exists")

    permission = Permission(
        name=perm_data.name,
        description=perm_data.description,
        resource=perm_data.resource.value,
        action=perm_data.action.value,
    )
    db.add(permission)
    await db.flush()

    # Audit log
    audit = AuditLogger(db)
    await audit.log(
        action=AuditAction.CREATE,
        resource_type=ResourceType.ROLE,  # permissions are part of role management
        resource_id=str(permission.id),
        user=current_user,
        ip_address=_get_client_ip(request),
        details={"permission_name": permission.name},
    )

    return permission


# ============================================================================
# Audit Log Queries
# ============================================================================


@router.get(
    "/audit-logs",
    response_model=list[AuditLogRead],
    dependencies=[Depends(require_permission("audit_log", "read"))],
)
async def list_audit_logs(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user_id: UUID | None = None,
    resource_type: ResourceType | None = None,
    resource_id: str | None = None,
    action: AuditAction | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
) -> list[AuditLogRead]:
    """
    Query audit logs with filters (requires audit_log:read permission).

    Audit logs are immutable and can only be read, never modified.
    """
    audit = AuditLogger(db)
    return await audit.get_logs(
        user_id=user_id,
        resource_type=resource_type,
        resource_id=resource_id,
        action=action,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
        offset=skip,
    )


@router.get(
    "/audit-logs/user/{user_id}",
    response_model=list[AuditLogRead],
    dependencies=[Depends(require_permission("audit_log", "read"))],
)
async def get_user_audit_logs(
    user_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    limit: int = Query(100, ge=1, le=500),
) -> list[AuditLogRead]:
    """Get all audit logs for a specific user (requires audit_log:read permission)."""
    audit = AuditLogger(db)
    return await audit.get_user_activity(user_id, limit=limit)


@router.get(
    "/audit-logs/resource/{resource_type}/{resource_id}",
    response_model=list[AuditLogRead],
    dependencies=[Depends(require_permission("audit_log", "read"))],
)
async def get_resource_audit_logs(
    resource_type: ResourceType,
    resource_id: str,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    limit: int = Query(50, ge=1, le=500),
) -> list[AuditLogRead]:
    """Get all audit logs for a specific resource (requires audit_log:read permission)."""
    audit = AuditLogger(db)
    return await audit.get_logs_for_resource(resource_type, resource_id, limit=limit)
