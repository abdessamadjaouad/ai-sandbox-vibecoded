# tests/unit/test_governance/test_audit.py
"""Tests for audit logging service."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from backend.app.governance.audit import AuditLogger, _mask_sensitive_fields
from backend.app.governance.models import (
    AuditAction,
    AuditLog,
    AuditLogRead,
    ResourceType,
    User,
)


class TestMaskSensitiveFields:
    """Tests for sensitive field masking."""

    def test_mask_password_field(self):
        """Test password fields are masked."""
        data = {"username": "john", "password": "secret123"}
        masked = _mask_sensitive_fields(data)

        assert masked["username"] == "john"
        assert masked["password"] == "***MASKED***"

    def test_mask_multiple_sensitive_fields(self):
        """Test multiple sensitive fields are masked."""
        data = {
            "api_key": "abc123",
            "secret_key": "xyz789",
            "access_key": "key456",
            "user": "admin",
        }
        masked = _mask_sensitive_fields(data)

        assert masked["api_key"] == "***MASKED***"
        assert masked["secret_key"] == "***MASKED***"
        assert masked["access_key"] == "***MASKED***"
        assert masked["user"] == "admin"

    def test_mask_nested_sensitive_fields(self):
        """Test nested sensitive fields are masked."""
        data = {
            "config": {
                "database_password": "db_secret",
                "host": "localhost",
            },
            "name": "app",
        }
        masked = _mask_sensitive_fields(data)

        assert masked["config"]["database_password"] == "***MASKED***"
        assert masked["config"]["host"] == "localhost"
        assert masked["name"] == "app"

    def test_mask_case_insensitive(self):
        """Test masking is case insensitive."""
        data = {
            "PASSWORD": "secret1",
            "API_KEY": "secret2",
            "Secret": "secret3",
        }
        masked = _mask_sensitive_fields(data)

        assert masked["PASSWORD"] == "***MASKED***"
        assert masked["API_KEY"] == "***MASKED***"
        assert masked["Secret"] == "***MASKED***"

    def test_mask_partial_match(self):
        """Test partial key matches are masked."""
        data = {
            "user_password_hash": "hash123",
            "db_secret_value": "value456",
        }
        masked = _mask_sensitive_fields(data)

        assert masked["user_password_hash"] == "***MASKED***"
        assert masked["db_secret_value"] == "***MASKED***"

    def test_mask_none_input(self):
        """Test None input returns None."""
        assert _mask_sensitive_fields(None) is None

    def test_mask_empty_dict(self):
        """Test empty dict returns empty dict."""
        assert _mask_sensitive_fields({}) == {}


class TestAuditLogger:
    """Tests for AuditLogger class."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = AsyncMock()
        db.add = MagicMock()
        db.flush = AsyncMock()
        return db

    @pytest.fixture
    def mock_user(self):
        """Create a mock user."""
        user = MagicMock(spec=User)
        user.id = uuid4()
        user.username = "testuser"
        return user

    @pytest.mark.asyncio
    async def test_log_basic(self, mock_db):
        """Test basic audit log creation."""
        audit = AuditLogger(mock_db)

        log = await audit.log(
            action=AuditAction.CREATE,
            resource_type=ResourceType.DATASET,
            resource_id="dataset-123",
        )

        mock_db.add.assert_called_once()
        mock_db.flush.assert_awaited_once()
        assert isinstance(log, AuditLog)
        assert log.action == "create"
        assert log.resource_type == "dataset"
        assert log.resource_id == "dataset-123"

    @pytest.mark.asyncio
    async def test_log_with_user(self, mock_db, mock_user):
        """Test audit log with user information."""
        audit = AuditLogger(mock_db)

        log = await audit.log(
            action=AuditAction.READ,
            resource_type=ResourceType.EXPERIMENT,
            resource_id="exp-456",
            user=mock_user,
        )

        assert log.user_id == mock_user.id
        assert log.username == mock_user.username

    @pytest.mark.asyncio
    async def test_log_masks_sensitive_details(self, mock_db):
        """Test sensitive fields in details are masked."""
        audit = AuditLogger(mock_db)

        log = await audit.log(
            action=AuditAction.UPDATE,
            resource_type=ResourceType.USER,
            details={"email": "user@test.com", "password": "secret123"},
        )

        assert log.details["email"] == "user@test.com"
        assert log.details["password"] == "***MASKED***"

    @pytest.mark.asyncio
    async def test_log_with_all_fields(self, mock_db, mock_user):
        """Test audit log with all fields populated."""
        audit = AuditLogger(mock_db)

        log = await audit.log(
            action=AuditAction.DELETE,
            resource_type=ResourceType.MODEL,
            resource_id="model-789",
            user=mock_user,
            ip_address="192.168.1.100",
            details={"model_name": "test-model"},
            status="success",
            request_id="req-abc",
            session_id="sess-xyz",
        )

        assert log.ip_address == "192.168.1.100"
        assert log.request_id == "req-abc"
        assert log.session_id == "sess-xyz"
        assert log.status == "success"

    @pytest.mark.asyncio
    async def test_log_login_success(self, mock_db, mock_user):
        """Test logging successful login."""
        audit = AuditLogger(mock_db)

        log = await audit.log_login(
            user=mock_user,
            ip_address="10.0.0.1",
            success=True,
        )

        assert log.action == "login"
        assert log.resource_type == "user"
        assert log.status == "success"

    @pytest.mark.asyncio
    async def test_log_login_failure(self, mock_db, mock_user):
        """Test logging failed login."""
        audit = AuditLogger(mock_db)

        log = await audit.log_login(
            user=mock_user,
            success=False,
            error_message="Invalid password",
        )

        assert log.action == "failed_login"
        assert log.status == "failure"
        assert log.error_message == "Invalid password"

    @pytest.mark.asyncio
    async def test_log_logout(self, mock_db, mock_user):
        """Test logging logout."""
        audit = AuditLogger(mock_db)

        log = await audit.log_logout(user=mock_user)

        assert log.action == "logout"
        assert log.resource_type == "user"

    @pytest.mark.asyncio
    async def test_log_permission_denied(self, mock_db, mock_user):
        """Test logging permission denied event."""
        audit = AuditLogger(mock_db)

        log = await audit.log_permission_denied(
            user=mock_user,
            resource_type=ResourceType.DATASET,
            action="delete",
            resource_id="dataset-protected",
        )

        assert log.action == "permission_denied"
        assert log.status == "failure"
        assert log.details["attempted_action"] == "delete"

    @pytest.mark.asyncio
    async def test_get_logs_basic(self, mock_db):
        """Test basic log retrieval."""
        mock_logs = [MagicMock(spec=AuditLog) for _ in range(3)]
        for i, log in enumerate(mock_logs):
            log.id = uuid4()
            log.timestamp = datetime.now(timezone.utc)
            log.user_id = uuid4()
            log.username = f"user{i}"
            log.ip_address = None
            log.action = "read"
            log.resource_type = "dataset"
            log.resource_id = f"ds-{i}"
            log.details = None
            log.status = "success"
            log.error_message = None
            log.request_id = None

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_logs
        mock_db.execute = AsyncMock(return_value=mock_result)

        audit = AuditLogger(mock_db)
        logs = await audit.get_logs(limit=10)

        assert len(logs) == 3
        assert all(isinstance(log, AuditLogRead) for log in logs)

    @pytest.mark.asyncio
    async def test_get_logs_with_filters(self, mock_db):
        """Test log retrieval with filters."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        audit = AuditLogger(mock_db)
        user_id = uuid4()

        await audit.get_logs(
            user_id=user_id,
            resource_type=ResourceType.EXPERIMENT,
            action=AuditAction.CREATE,
            limit=50,
            offset=10,
        )

        # Verify execute was called (filters are applied in the query)
        mock_db.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_logs_for_resource(self, mock_db):
        """Test getting logs for a specific resource."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        audit = AuditLogger(mock_db)

        await audit.get_logs_for_resource(
            resource_type=ResourceType.DATASET,
            resource_id="ds-123",
            limit=20,
        )

        mock_db.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_user_activity(self, mock_db):
        """Test getting all activity for a user."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        audit = AuditLogger(mock_db)
        user_id = uuid4()

        await audit.get_user_activity(user_id, limit=100)

        mock_db.execute.assert_awaited_once()


class TestAuditLogModel:
    """Tests for AuditLog model representations."""

    def test_audit_log_repr(self):
        """Test AuditLog string representation."""
        log = AuditLog(
            action="create",
            resource_type="dataset",
            resource_id="ds-123",
        )

        repr_str = repr(log)
        assert "create" in repr_str
        assert "dataset" in repr_str
        assert "ds-123" in repr_str
