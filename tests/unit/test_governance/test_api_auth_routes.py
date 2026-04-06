# tests/unit/test_governance/test_api_auth_routes.py
"""Tests for authentication API routes."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from backend.app.governance.models import (
    AuditAction,
    Permission,
    ResourceType,
    Role,
    User,
)
from backend.app.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_user():
    """Create a mock user."""
    user = MagicMock(spec=User)
    user.id = uuid4()
    user.email = "test@example.com"
    user.username = "testuser"
    user.full_name = "Test User"
    user.hashed_password = "$2b$12$test_hash"
    user.is_active = True
    user.is_superuser = False
    user.role_id = None
    user.role = None
    user.created_at = MagicMock()
    user.updated_at = MagicMock()
    user.has_permission = MagicMock(return_value=True)
    return user


@pytest.fixture
def mock_superuser():
    """Create a mock superuser."""
    user = MagicMock(spec=User)
    user.id = uuid4()
    user.email = "admin@example.com"
    user.username = "admin"
    user.full_name = "Admin User"
    user.hashed_password = "$2b$12$admin_hash"
    user.is_active = True
    user.is_superuser = True
    user.role_id = None
    user.role = None
    user.created_at = MagicMock()
    user.updated_at = MagicMock()
    user.has_permission = MagicMock(return_value=True)
    return user


class TestRegisterEndpoint:
    """Tests for POST /api/v1/auth/register."""

    def test_register_invalid_email(self, client):
        """Test registration with invalid email."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "username": "testuser",
                "password": "secure_password",
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_short_password(self, client):
        """Test registration with short password."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser",
                "password": "short",
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_missing_username(self, client):
        """Test registration without username."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "secure_password_123",
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestLoginEndpoint:
    """Tests for POST /api/v1/auth/login."""

    def test_login_invalid_credentials_format(self, client):
        """Test login with invalid format returns 422."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "test", "password": "test"},  # Should be form data
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestMeEndpoint:
    """Tests for /api/v1/auth/me endpoints."""

    def test_me_unauthenticated(self, client):
        """Test /me endpoint without authentication."""
        response = client.get("/api/v1/auth/me")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_me_invalid_token(self, client):
        """Test /me endpoint with invalid token."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestUserManagementEndpoints:
    """Tests for user management endpoints."""

    def test_list_users_unauthenticated(self, client):
        """Test listing users without authentication."""
        response = client.get("/api/v1/auth/users")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_user_unauthenticated(self, client):
        """Test getting user without authentication."""
        user_id = uuid4()
        response = client.get(f"/api/v1/auth/users/{user_id}")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_delete_user_unauthenticated(self, client):
        """Test deleting user without authentication."""
        user_id = uuid4()
        response = client.delete(f"/api/v1/auth/users/{user_id}")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestRoleEndpoints:
    """Tests for role management endpoints."""

    def test_list_roles_unauthenticated(self, client):
        """Test listing roles without authentication."""
        response = client.get("/api/v1/auth/roles")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_role_unauthenticated(self, client):
        """Test creating role without authentication."""
        response = client.post(
            "/api/v1/auth/roles",
            json={"name": "test_role", "description": "Test role"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestPermissionEndpoints:
    """Tests for permission management endpoints."""

    def test_list_permissions_unauthenticated(self, client):
        """Test listing permissions without authentication."""
        response = client.get("/api/v1/auth/permissions")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestAuditLogEndpoints:
    """Tests for audit log query endpoints."""

    def test_list_audit_logs_unauthenticated(self, client):
        """Test listing audit logs without authentication."""
        response = client.get("/api/v1/auth/audit-logs")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_user_audit_logs_unauthenticated(self, client):
        """Test getting user audit logs without authentication."""
        user_id = uuid4()
        response = client.get(f"/api/v1/auth/audit-logs/user/{user_id}")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_resource_audit_logs_unauthenticated(self, client):
        """Test getting resource audit logs without authentication."""
        response = client.get("/api/v1/auth/audit-logs/resource/dataset/ds-123")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestLogoutEndpoint:
    """Tests for POST /api/v1/auth/logout."""

    def test_logout_unauthenticated(self, client):
        """Test logout without authentication."""
        response = client.post("/api/v1/auth/logout")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
