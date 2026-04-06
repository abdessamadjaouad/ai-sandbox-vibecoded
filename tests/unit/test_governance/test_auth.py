# tests/unit/test_governance/test_auth.py
"""Tests for authentication service."""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from backend.app.governance.auth import AuthService
from backend.app.governance.models import Permission, Role, Token, TokenPayload, User


class TestAuthService:
    """Tests for AuthService class."""

    def test_hash_password(self):
        """Test password hashing produces valid bcrypt hash."""
        password = "my_secure_password_123"
        hashed = AuthService.hash_password(password)

        assert hashed != password
        assert hashed.startswith("$2b$")
        assert len(hashed) == 60

    def test_hash_password_different_hashes(self):
        """Test same password produces different hashes (salt)."""
        password = "same_password"
        hash1 = AuthService.hash_password(password)
        hash2 = AuthService.hash_password(password)

        assert hash1 != hash2

    def test_verify_password_correct(self):
        """Test correct password verification."""
        password = "test_password_456"
        hashed = AuthService.hash_password(password)

        assert AuthService.verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test incorrect password verification."""
        password = "correct_password"
        wrong_password = "wrong_password"
        hashed = AuthService.hash_password(password)

        assert AuthService.verify_password(wrong_password, hashed) is False

    def test_create_access_token(self):
        """Test JWT token creation."""
        # Create mock user
        user = MagicMock(spec=User)
        user.id = uuid4()
        user.username = "testuser"
        user.email = "test@example.com"
        user.is_superuser = False
        user.role = None

        token = AuthService.create_access_token(user)

        assert isinstance(token, Token)
        assert token.token_type == "bearer"
        assert token.access_token
        assert len(token.access_token) > 50

    def test_create_access_token_with_permissions(self):
        """Test JWT token includes permissions from role."""
        # Create mock permission
        perm = MagicMock(spec=Permission)
        perm.resource = "dataset"
        perm.action = "read"

        # Create mock role with permission
        role = MagicMock(spec=Role)
        role.permissions = [perm]

        # Create mock user with role
        user = MagicMock(spec=User)
        user.id = uuid4()
        user.username = "roleuser"
        user.email = "role@example.com"
        user.is_superuser = False
        user.role = role

        token = AuthService.create_access_token(user)
        payload = AuthService.decode_token(token.access_token)

        assert payload is not None
        assert "dataset:read" in payload.permissions

    def test_create_access_token_with_custom_expiry(self):
        """Test JWT token with custom expiration."""
        user = MagicMock(spec=User)
        user.id = uuid4()
        user.username = "expiryuser"
        user.email = "expiry@example.com"
        user.is_superuser = False
        user.role = None

        custom_delta = timedelta(minutes=5)
        token = AuthService.create_access_token(user, expires_delta=custom_delta)
        payload = AuthService.decode_token(token.access_token)

        assert payload is not None
        assert payload.exp is not None
        # Token should expire within ~5 minutes
        expected_exp = datetime.now(timezone.utc) + custom_delta
        assert abs((payload.exp - expected_exp).total_seconds()) < 5

    def test_decode_token_valid(self):
        """Test decoding a valid token."""
        user = MagicMock(spec=User)
        user.id = uuid4()
        user.username = "decodeuser"
        user.email = "decode@example.com"
        user.is_superuser = True
        user.role = None

        token = AuthService.create_access_token(user)
        payload = AuthService.decode_token(token.access_token)

        assert payload is not None
        assert payload.sub == str(user.id)
        assert payload.username == "decodeuser"
        assert payload.email == "decode@example.com"
        assert payload.is_superuser is True

    def test_decode_token_invalid(self):
        """Test decoding an invalid token returns None."""
        payload = AuthService.decode_token("invalid.token.string")
        assert payload is None

    def test_decode_token_tampered(self):
        """Test decoding a tampered token returns None."""
        user = MagicMock(spec=User)
        user.id = uuid4()
        user.username = "tampereduser"
        user.email = "tampered@example.com"
        user.is_superuser = False
        user.role = None

        token = AuthService.create_access_token(user)
        # Tamper with the token
        tampered = token.access_token[:-5] + "XXXXX"

        payload = AuthService.decode_token(tampered)
        assert payload is None


class TestUserPermissions:
    """Tests for user permission checking."""

    def test_superuser_has_all_permissions(self):
        """Test superuser has all permissions."""
        user = MagicMock(spec=User)
        user.is_superuser = True
        user.role = None
        user.has_permission = User.has_permission.__get__(user, User)

        assert user.has_permission("dataset", "read") is True
        assert user.has_permission("experiment", "delete") is True
        assert user.has_permission("system", "execute") is True

    def test_user_with_role_permission(self):
        """Test user has permission via role."""
        perm = MagicMock(spec=Permission)
        perm.resource = "dataset"
        perm.action = "read"

        role = MagicMock(spec=Role)
        role.permissions = [perm]
        role.has_permission = Role.has_permission.__get__(role, Role)

        user = MagicMock(spec=User)
        user.is_superuser = False
        user.role = role
        user.has_permission = User.has_permission.__get__(user, User)

        assert user.has_permission("dataset", "read") is True
        assert user.has_permission("dataset", "delete") is False

    def test_user_without_role(self):
        """Test user without role has no permissions."""
        user = MagicMock(spec=User)
        user.is_superuser = False
        user.role = None
        user.has_permission = User.has_permission.__get__(user, User)

        assert user.has_permission("dataset", "read") is False

    def test_role_system_execute_grants_all(self):
        """Test system:execute permission grants all access."""
        system_perm = MagicMock(spec=Permission)
        system_perm.resource = "system"
        system_perm.action = "execute"

        role = MagicMock(spec=Role)
        role.permissions = [system_perm]
        role.has_permission = Role.has_permission.__get__(role, Role)

        assert role.has_permission("dataset", "delete") is True
        assert role.has_permission("experiment", "execute") is True
        assert role.has_permission("anything", "anything") is True


class TestTokenPayload:
    """Tests for TokenPayload schema."""

    def test_token_payload_creation(self):
        """Test TokenPayload can be created."""
        payload = TokenPayload(
            sub="user-123",
            username="testuser",
            email="test@example.com",
            is_superuser=False,
            permissions=["dataset:read", "experiment:create"],
        )

        assert payload.sub == "user-123"
        assert payload.username == "testuser"
        assert payload.is_superuser is False
        assert len(payload.permissions) == 2

    def test_token_payload_defaults(self):
        """Test TokenPayload default values."""
        payload = TokenPayload(
            sub="user-456",
            username="defaultuser",
            email="default@example.com",
        )

        assert payload.is_superuser is False
        assert payload.permissions == []
        assert payload.exp is None
