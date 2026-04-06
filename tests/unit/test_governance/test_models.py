# tests/unit/test_governance/test_models.py
"""Tests for governance models and schemas."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from backend.app.governance.models import (
    AuditAction,
    AuditLogCreate,
    Permission,
    PermissionAction,
    PermissionCreate,
    ResourceType,
    Role,
    RoleCreate,
    User,
    UserCreate,
    UserUpdate,
)


class TestEnums:
    """Tests for governance enums."""

    def test_permission_action_values(self):
        """Test PermissionAction enum values."""
        assert PermissionAction.CREATE.value == "create"
        assert PermissionAction.READ.value == "read"
        assert PermissionAction.UPDATE.value == "update"
        assert PermissionAction.DELETE.value == "delete"
        assert PermissionAction.EXECUTE.value == "execute"

    def test_resource_type_values(self):
        """Test ResourceType enum values."""
        assert ResourceType.DATASET.value == "dataset"
        assert ResourceType.EXPERIMENT.value == "experiment"
        assert ResourceType.MODEL.value == "model"
        assert ResourceType.USER.value == "user"
        assert ResourceType.ROLE.value == "role"
        assert ResourceType.AUDIT_LOG.value == "audit_log"
        assert ResourceType.SYSTEM.value == "system"

    def test_audit_action_values(self):
        """Test AuditAction enum values."""
        assert AuditAction.LOGIN.value == "login"
        assert AuditAction.LOGOUT.value == "logout"
        assert AuditAction.FAILED_LOGIN.value == "failed_login"
        assert AuditAction.PERMISSION_DENIED.value == "permission_denied"


class TestUserCreate:
    """Tests for UserCreate schema."""

    def test_valid_user_create(self):
        """Test creating a valid user."""
        user = UserCreate(
            email="test@example.com",
            username="testuser",
            password="secure_password_123",
            full_name="Test User",
        )

        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.password == "secure_password_123"

    def test_user_create_invalid_email(self):
        """Test invalid email is rejected."""
        with pytest.raises(ValidationError):
            UserCreate(
                email="not-an-email",
                username="testuser",
                password="secure_password",
            )

    def test_user_create_short_username(self):
        """Test short username is rejected."""
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@example.com",
                username="ab",  # too short (min 3)
                password="secure_password",
            )

    def test_user_create_short_password(self):
        """Test short password is rejected."""
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@example.com",
                username="testuser",
                password="short",  # too short (min 8)
            )

    def test_user_create_with_role_id(self):
        """Test creating user with role ID."""
        role_id = uuid4()
        user = UserCreate(
            email="test@example.com",
            username="testuser",
            password="secure_password",
            role_id=role_id,
        )

        assert user.role_id == role_id


class TestUserUpdate:
    """Tests for UserUpdate schema."""

    def test_partial_update(self):
        """Test partial update with some fields."""
        update = UserUpdate(full_name="New Name")

        data = update.model_dump(exclude_unset=True)
        assert data == {"full_name": "New Name"}

    def test_update_email(self):
        """Test updating email."""
        update = UserUpdate(email="new@example.com")

        assert update.email == "new@example.com"

    def test_update_invalid_email(self):
        """Test invalid email in update is rejected."""
        with pytest.raises(ValidationError):
            UserUpdate(email="invalid-email")

    def test_update_is_active(self):
        """Test updating is_active status."""
        update = UserUpdate(is_active=False)

        assert update.is_active is False


class TestRoleCreate:
    """Tests for RoleCreate schema."""

    def test_valid_role_create(self):
        """Test creating a valid role."""
        role = RoleCreate(
            name="editor",
            description="Can edit datasets",
            permission_ids=[uuid4(), uuid4()],
        )

        assert role.name == "editor"
        assert role.description == "Can edit datasets"
        assert len(role.permission_ids) == 2

    def test_role_create_minimal(self):
        """Test creating role with minimal fields."""
        role = RoleCreate(name="viewer")

        assert role.name == "viewer"
        assert role.description is None
        assert role.permission_ids == []

    def test_role_create_empty_name(self):
        """Test empty name is rejected."""
        with pytest.raises(ValidationError):
            RoleCreate(name="")


class TestPermissionCreate:
    """Tests for PermissionCreate schema."""

    def test_valid_permission_create(self):
        """Test creating a valid permission."""
        perm = PermissionCreate(
            name="dataset:read",
            description="Can read datasets",
            resource=ResourceType.DATASET,
            action=PermissionAction.READ,
        )

        assert perm.name == "dataset:read"
        assert perm.resource == ResourceType.DATASET
        assert perm.action == PermissionAction.READ

    def test_permission_create_invalid_resource(self):
        """Test invalid resource type is rejected."""
        with pytest.raises(ValidationError):
            PermissionCreate(
                name="invalid:read",
                resource="invalid_resource",  # type: ignore
                action=PermissionAction.READ,
            )


class TestAuditLogCreate:
    """Tests for AuditLogCreate schema."""

    def test_valid_audit_log_create(self):
        """Test creating a valid audit log entry."""
        log = AuditLogCreate(
            action=AuditAction.CREATE,
            resource_type=ResourceType.DATASET,
            resource_id="ds-123",
            user_id=uuid4(),
            username="admin",
        )

        assert log.action == AuditAction.CREATE
        assert log.resource_type == ResourceType.DATASET
        assert log.resource_id == "ds-123"

    def test_audit_log_create_with_details(self):
        """Test audit log with details."""
        log = AuditLogCreate(
            action=AuditAction.UPDATE,
            resource_type=ResourceType.EXPERIMENT,
            details={"old_value": 1, "new_value": 2},
        )

        assert log.details == {"old_value": 1, "new_value": 2}

    def test_audit_log_create_defaults(self):
        """Test audit log default values."""
        log = AuditLogCreate(
            action=AuditAction.READ,
            resource_type=ResourceType.MODEL,
        )

        assert log.status == "success"
        assert log.user_id is None
        assert log.ip_address is None


class TestModelRelationships:
    """Tests for model relationship methods."""

    def test_role_has_permission_direct(self):
        """Test Role.has_permission with direct permission."""
        perm = Permission(
            name="test_perm",
            resource="dataset",
            action="read",
        )
        role = Role(name="test_role", permissions=[perm])

        assert role.has_permission("dataset", "read") is True
        assert role.has_permission("dataset", "delete") is False

    def test_role_has_permission_system_wildcard(self):
        """Test Role.has_permission with system:execute wildcard."""
        system_perm = Permission(
            name="system_admin",
            resource="system",
            action="execute",
        )
        role = Role(name="admin", permissions=[system_perm])

        # system:execute grants all permissions
        assert role.has_permission("dataset", "delete") is True
        assert role.has_permission("any", "thing") is True

    def test_role_has_permission_no_permissions(self):
        """Test Role.has_permission with no permissions."""
        role = Role(name="empty_role", permissions=[])

        assert role.has_permission("dataset", "read") is False

    def test_user_has_permission_superuser(self):
        """Test User.has_permission for superuser."""
        user = User(
            email="super@test.com",
            username="superuser",
            hashed_password="hash",
            is_superuser=True,
        )

        # Superuser has all permissions
        assert user.has_permission("anything", "anything") is True

    def test_user_has_permission_via_role(self):
        """Test User.has_permission via role."""
        perm = Permission(
            name="exp_read",
            resource="experiment",
            action="read",
        )
        role = Role(name="researcher", permissions=[perm])
        user = User(
            email="researcher@test.com",
            username="researcher",
            hashed_password="hash",
            is_superuser=False,
            role=role,
        )

        assert user.has_permission("experiment", "read") is True
        assert user.has_permission("experiment", "delete") is False

    def test_user_has_permission_no_role(self):
        """Test User.has_permission without role."""
        user = User(
            email="norole@test.com",
            username="norole",
            hashed_password="hash",
            is_superuser=False,
            role=None,
        )

        assert user.has_permission("dataset", "read") is False


class TestModelRepresentations:
    """Tests for model __repr__ methods."""

    def test_permission_repr(self):
        """Test Permission string representation."""
        perm = Permission(name="test_permission", resource="dataset", action="read")
        assert "test_permission" in repr(perm)

    def test_role_repr(self):
        """Test Role string representation."""
        role = Role(name="test_role")
        assert "test_role" in repr(role)

    def test_user_repr(self):
        """Test User string representation."""
        user = User(
            email="test@test.com",
            username="testuser",
            hashed_password="hash",
        )
        assert "testuser" in repr(user)
