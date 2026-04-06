# backend/app/governance/audit.py
"""
Immutable audit logging service.

Provides structured audit logging for all sensitive operations.
Audit logs are append-only and cannot be modified or deleted through the API.
"""

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.logging import get_logger
from backend.app.governance.models import (
    AuditAction,
    AuditLog,
    AuditLogCreate,
    AuditLogRead,
    ResourceType,
    User,
)

logger = get_logger(__name__)


def _mask_sensitive_fields(data: dict[str, Any] | None) -> dict[str, Any] | None:
    """
    Mask sensitive fields in audit log details.

    Args:
        data: Dictionary that may contain sensitive fields

    Returns:
        Dictionary with sensitive fields masked
    """
    if not data:
        return data

    sensitive_keys = {
        "password",
        "hashed_password",
        "secret",
        "token",
        "api_key",
        "access_key",
        "secret_key",
        "credit_card",
        "ssn",
        "social_security",
    }

    masked = {}
    for key, value in data.items():
        lower_key = key.lower()
        if any(sensitive in lower_key for sensitive in sensitive_keys):
            masked[key] = "***MASKED***"
        elif isinstance(value, dict):
            masked[key] = _mask_sensitive_fields(value)
        else:
            masked[key] = value

    return masked


class AuditLogger:
    """
    Service for creating and querying audit logs.

    Audit logs are immutable - they can only be created and read, never modified or deleted.
    All sensitive fields are automatically masked before storage.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize the audit logger.

        Args:
            db: Async database session
        """
        self.db = db

    async def log(
        self,
        action: AuditAction,
        resource_type: ResourceType,
        resource_id: str | None = None,
        user: User | None = None,
        user_id: UUID | None = None,
        username: str | None = None,
        ip_address: str | None = None,
        details: dict[str, Any] | None = None,
        status: str = "success",
        error_message: str | None = None,
        request_id: str | None = None,
        session_id: str | None = None,
    ) -> AuditLog:
        """
        Create an immutable audit log entry.

        Args:
            action: The action being logged (create, read, update, delete, etc.)
            resource_type: Type of resource being accessed
            resource_id: ID of the specific resource (optional)
            user: User object performing the action (optional)
            user_id: User ID if user object not provided
            username: Username if user object not provided
            ip_address: Client IP address
            details: Additional context (sensitive fields will be masked)
            status: Operation status (success/failure)
            error_message: Error details if operation failed
            request_id: Correlation ID for request tracing
            session_id: User session ID

        Returns:
            Created AuditLog entry
        """
        # Extract user info from User object if provided
        if user:
            user_id = user.id
            username = user.username

        # Mask sensitive fields in details
        masked_details = _mask_sensitive_fields(details)

        audit_log = AuditLog(
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            action=action.value,
            resource_type=resource_type.value,
            resource_id=resource_id,
            details=masked_details,
            status=status,
            error_message=error_message,
            request_id=request_id,
            session_id=session_id,
        )

        self.db.add(audit_log)
        await self.db.flush()

        # Also log to structured logger for real-time monitoring
        logger.info(
            "audit_log_created",
            audit_id=str(audit_log.id),
            action=action.value,
            resource_type=resource_type.value,
            resource_id=resource_id,
            user_id=str(user_id) if user_id else None,
            username=username,
            status=status,
        )

        return audit_log

    async def log_login(
        self,
        user: User,
        ip_address: str | None = None,
        success: bool = True,
        error_message: str | None = None,
    ) -> AuditLog:
        """
        Log a login attempt.

        Args:
            user: User attempting to login
            ip_address: Client IP address
            success: Whether login was successful
            error_message: Error message if login failed

        Returns:
            Created AuditLog entry
        """
        return await self.log(
            action=AuditAction.LOGIN if success else AuditAction.FAILED_LOGIN,
            resource_type=ResourceType.USER,
            resource_id=str(user.id),
            user=user,
            ip_address=ip_address,
            status="success" if success else "failure",
            error_message=error_message,
        )

    async def log_logout(
        self,
        user: User,
        ip_address: str | None = None,
    ) -> AuditLog:
        """
        Log a logout event.

        Args:
            user: User logging out
            ip_address: Client IP address

        Returns:
            Created AuditLog entry
        """
        return await self.log(
            action=AuditAction.LOGOUT,
            resource_type=ResourceType.USER,
            resource_id=str(user.id),
            user=user,
            ip_address=ip_address,
        )

    async def log_permission_denied(
        self,
        user: User,
        resource_type: ResourceType,
        action: str,
        resource_id: str | None = None,
        ip_address: str | None = None,
    ) -> AuditLog:
        """
        Log a permission denied event.

        Args:
            user: User who was denied
            resource_type: Resource they tried to access
            action: Action they tried to perform
            resource_id: Specific resource ID
            ip_address: Client IP address

        Returns:
            Created AuditLog entry
        """
        return await self.log(
            action=AuditAction.PERMISSION_DENIED,
            resource_type=resource_type,
            resource_id=resource_id,
            user=user,
            ip_address=ip_address,
            status="failure",
            details={"attempted_action": action},
        )

    async def get_logs(
        self,
        user_id: UUID | None = None,
        resource_type: ResourceType | None = None,
        resource_id: str | None = None,
        action: AuditAction | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditLogRead]:
        """
        Query audit logs with filters.

        Args:
            user_id: Filter by user ID
            resource_type: Filter by resource type
            resource_id: Filter by resource ID
            action: Filter by action
            start_time: Filter by start time (inclusive)
            end_time: Filter by end time (inclusive)
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of matching audit log entries
        """
        stmt = select(AuditLog).order_by(AuditLog.timestamp.desc())

        if user_id:
            stmt = stmt.where(AuditLog.user_id == user_id)
        if resource_type:
            stmt = stmt.where(AuditLog.resource_type == resource_type.value)
        if resource_id:
            stmt = stmt.where(AuditLog.resource_id == resource_id)
        if action:
            stmt = stmt.where(AuditLog.action == action.value)
        if start_time:
            stmt = stmt.where(AuditLog.timestamp >= start_time)
        if end_time:
            stmt = stmt.where(AuditLog.timestamp <= end_time)

        stmt = stmt.limit(limit).offset(offset)

        result = await self.db.execute(stmt)
        logs = result.scalars().all()

        return [AuditLogRead.model_validate(log) for log in logs]

    async def get_logs_for_resource(
        self,
        resource_type: ResourceType,
        resource_id: str,
        limit: int = 50,
    ) -> list[AuditLogRead]:
        """
        Get all audit logs for a specific resource.

        Args:
            resource_type: Type of resource
            resource_id: ID of the resource
            limit: Maximum number of results

        Returns:
            List of audit log entries for the resource
        """
        return await self.get_logs(
            resource_type=resource_type,
            resource_id=resource_id,
            limit=limit,
        )

    async def get_user_activity(
        self,
        user_id: UUID,
        limit: int = 100,
    ) -> list[AuditLogRead]:
        """
        Get all activity for a specific user.

        Args:
            user_id: ID of the user
            limit: Maximum number of results

        Returns:
            List of audit log entries for the user
        """
        return await self.get_logs(
            user_id=user_id,
            limit=limit,
        )
