# tests/unit/test_governance/test_secrets.py
"""Tests for secrets management service."""

import os
import tempfile
from pathlib import Path

import pytest

from backend.app.governance.secrets import (
    EnvironmentSecretsBackend,
    FileSecretsBackend,
    SecretsManager,
    VaultSecretsBackend,
    get_secret,
)


class TestEnvironmentSecretsBackend:
    """Tests for environment variables backend."""

    def test_get_secret_exists(self):
        """Test getting an existing secret."""
        backend = EnvironmentSecretsBackend(prefix="TEST_SECRET_")
        os.environ["TEST_SECRET_MY_KEY"] = "my_value"

        try:
            value = backend.get_secret("my-key")
            assert value == "my_value"
        finally:
            del os.environ["TEST_SECRET_MY_KEY"]

    def test_get_secret_not_exists(self):
        """Test getting a non-existent secret."""
        backend = EnvironmentSecretsBackend(prefix="TEST_SECRET_")

        value = backend.get_secret("nonexistent-key")
        assert value is None

    def test_get_secret_with_default(self):
        """Test getting a secret with default value."""
        backend = EnvironmentSecretsBackend(prefix="TEST_SECRET_")

        value = backend.get_secret("nonexistent", default="default_value")
        assert value == "default_value"

    def test_set_secret(self):
        """Test setting a secret."""
        backend = EnvironmentSecretsBackend(prefix="TEST_SECRET_")

        result = backend.set_secret("new-key", "new_value")

        try:
            assert result is True
            assert os.environ["TEST_SECRET_NEW_KEY"] == "new_value"
        finally:
            if "TEST_SECRET_NEW_KEY" in os.environ:
                del os.environ["TEST_SECRET_NEW_KEY"]

    def test_delete_secret_exists(self):
        """Test deleting an existing secret."""
        backend = EnvironmentSecretsBackend(prefix="TEST_SECRET_")
        os.environ["TEST_SECRET_DELETE_ME"] = "value"

        result = backend.delete_secret("delete-me")

        assert result is True
        assert "TEST_SECRET_DELETE_ME" not in os.environ

    def test_delete_secret_not_exists(self):
        """Test deleting a non-existent secret."""
        backend = EnvironmentSecretsBackend(prefix="TEST_SECRET_")

        result = backend.delete_secret("nonexistent")
        assert result is False

    def test_list_secrets(self):
        """Test listing secrets."""
        backend = EnvironmentSecretsBackend(prefix="TEST_LIST_")
        os.environ["TEST_LIST_KEY1"] = "val1"
        os.environ["TEST_LIST_KEY2"] = "val2"

        try:
            keys = backend.list_secrets()
            assert "key1" in keys
            assert "key2" in keys
        finally:
            del os.environ["TEST_LIST_KEY1"]
            del os.environ["TEST_LIST_KEY2"]

    def test_env_key_conversion(self):
        """Test key to environment variable conversion."""
        backend = EnvironmentSecretsBackend(prefix="PREFIX_")

        assert backend._env_key("my-key") == "PREFIX_MY_KEY"
        assert backend._env_key("my.key") == "PREFIX_MY_KEY"
        assert backend._env_key("MY_KEY") == "PREFIX_MY_KEY"


class TestFileSecretsBackend:
    """Tests for file-based backend."""

    @pytest.fixture
    def temp_secrets_dir(self):
        """Create a temporary secrets directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    def test_get_secret_exists(self, temp_secrets_dir):
        """Test getting an existing secret file."""
        backend = FileSecretsBackend(secrets_dir=temp_secrets_dir)

        # Create a secret file
        secret_path = Path(temp_secrets_dir) / "my-secret"
        secret_path.write_text("secret_value")

        value = backend.get_secret("my-secret")
        assert value == "secret_value"

    def test_get_secret_not_exists(self, temp_secrets_dir):
        """Test getting a non-existent secret file."""
        backend = FileSecretsBackend(secrets_dir=temp_secrets_dir)

        value = backend.get_secret("nonexistent")
        assert value is None

    def test_get_secret_with_default(self, temp_secrets_dir):
        """Test getting a secret with default."""
        backend = FileSecretsBackend(secrets_dir=temp_secrets_dir)

        value = backend.get_secret("nonexistent", default="default")
        assert value == "default"

    def test_get_secret_strips_whitespace(self, temp_secrets_dir):
        """Test that secret values are stripped."""
        backend = FileSecretsBackend(secrets_dir=temp_secrets_dir)

        secret_path = Path(temp_secrets_dir) / "whitespace-secret"
        secret_path.write_text("  value_with_spaces  \n")

        value = backend.get_secret("whitespace-secret")
        assert value == "value_with_spaces"

    def test_set_secret(self, temp_secrets_dir):
        """Test setting a secret file."""
        backend = FileSecretsBackend(secrets_dir=temp_secrets_dir)

        result = backend.set_secret("new-secret", "new_value")

        assert result is True
        secret_path = Path(temp_secrets_dir) / "new-secret"
        assert secret_path.exists()
        assert secret_path.read_text() == "new_value"

    def test_delete_secret_exists(self, temp_secrets_dir):
        """Test deleting an existing secret file."""
        backend = FileSecretsBackend(secrets_dir=temp_secrets_dir)

        secret_path = Path(temp_secrets_dir) / "delete-me"
        secret_path.write_text("value")

        result = backend.delete_secret("delete-me")

        assert result is True
        assert not secret_path.exists()

    def test_delete_secret_not_exists(self, temp_secrets_dir):
        """Test deleting a non-existent secret."""
        backend = FileSecretsBackend(secrets_dir=temp_secrets_dir)

        result = backend.delete_secret("nonexistent")
        assert result is False

    def test_list_secrets(self, temp_secrets_dir):
        """Test listing secret files."""
        backend = FileSecretsBackend(secrets_dir=temp_secrets_dir)

        # Create some secret files
        (Path(temp_secrets_dir) / "secret1").write_text("val1")
        (Path(temp_secrets_dir) / "secret2").write_text("val2")

        keys = backend.list_secrets()

        assert "secret1" in keys
        assert "secret2" in keys

    def test_list_secrets_empty_dir(self):
        """Test listing from non-existent directory."""
        backend = FileSecretsBackend(secrets_dir="/nonexistent/dir")

        keys = backend.list_secrets()
        assert keys == []

    def test_path_sanitization(self, temp_secrets_dir):
        """Test that path traversal is prevented."""
        backend = FileSecretsBackend(secrets_dir=temp_secrets_dir)

        # Attempt path traversal
        path = backend._secret_path("../../../etc/passwd")
        assert ".." not in path


class TestVaultSecretsBackend:
    """Tests for Vault backend (stub implementation)."""

    def test_init_without_credentials(self):
        """Test initialization without Vault credentials."""
        # Remove any existing Vault env vars for this test
        old_addr = os.environ.pop("VAULT_ADDR", None)
        old_token = os.environ.pop("VAULT_TOKEN", None)

        try:
            backend = VaultSecretsBackend()

            # Without credentials, should return defaults
            value = backend.get_secret("any-key", default="default")
            assert value == "default"
        finally:
            if old_addr:
                os.environ["VAULT_ADDR"] = old_addr
            if old_token:
                os.environ["VAULT_TOKEN"] = old_token

    def test_get_secret_unavailable(self):
        """Test getting secret when Vault is unavailable."""
        backend = VaultSecretsBackend()
        backend._available = False

        value = backend.get_secret("test-key", default="fallback")
        assert value == "fallback"

    def test_set_secret_unavailable(self):
        """Test setting secret when Vault is unavailable."""
        backend = VaultSecretsBackend()
        backend._available = False

        result = backend.set_secret("test-key", "value")
        assert result is False

    def test_list_secrets_unavailable(self):
        """Test listing secrets when Vault is unavailable."""
        backend = VaultSecretsBackend()
        backend._available = False

        keys = backend.list_secrets()
        assert keys == []


class TestSecretsManager:
    """Tests for the unified secrets manager."""

    @pytest.fixture
    def temp_secrets_dir(self):
        """Create a temporary secrets directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    def test_get_from_first_available_backend(self, temp_secrets_dir):
        """Test that secrets are retrieved from first available backend."""
        # Set up file backend with a secret
        secret_path = Path(temp_secrets_dir) / "test-secret"
        secret_path.write_text("file_value")

        file_backend = FileSecretsBackend(secrets_dir=temp_secrets_dir)
        env_backend = EnvironmentSecretsBackend(prefix="SM_TEST_")

        manager = SecretsManager(backends=[file_backend, env_backend])

        value = manager.get("test-secret")
        assert value == "file_value"

    def test_fallback_to_second_backend(self, temp_secrets_dir):
        """Test fallback when first backend doesn't have the secret."""
        file_backend = FileSecretsBackend(secrets_dir=temp_secrets_dir)
        env_backend = EnvironmentSecretsBackend(prefix="SM_FALLBACK_")

        os.environ["SM_FALLBACK_MY_KEY"] = "env_value"

        try:
            manager = SecretsManager(backends=[file_backend, env_backend])

            # File doesn't have it, should fall back to env
            value = manager.get("my-key")
            assert value == "env_value"
        finally:
            del os.environ["SM_FALLBACK_MY_KEY"]

    def test_get_with_default(self):
        """Test getting secret with default when not found."""
        manager = SecretsManager(backends=[EnvironmentSecretsBackend(prefix="EMPTY_")])

        value = manager.get("nonexistent", default="my_default")
        assert value == "my_default"

    def test_get_required_raises(self):
        """Test that required=True raises when not found."""
        manager = SecretsManager(backends=[EnvironmentSecretsBackend(prefix="EMPTY_")])

        with pytest.raises(ValueError) as exc_info:
            manager.get("required-key", required=True)

        assert "required-key" in str(exc_info.value)

    def test_get_required_with_default(self):
        """Test that required=True with default doesn't raise."""
        manager = SecretsManager(backends=[EnvironmentSecretsBackend(prefix="EMPTY_")])

        value = manager.get("key", default="provided", required=True)
        assert value == "provided"

    def test_set_to_specific_backend(self, temp_secrets_dir):
        """Test setting secret to a specific backend."""
        file_backend = FileSecretsBackend(secrets_dir=temp_secrets_dir)
        env_backend = EnvironmentSecretsBackend(prefix="SM_SET_")

        manager = SecretsManager(backends=[file_backend, env_backend])

        # Set to first backend (file)
        result = manager.set("new-secret", "new_value", backend_index=0)

        assert result is True
        assert (Path(temp_secrets_dir) / "new-secret").read_text() == "new_value"

    def test_delete_from_all_backends(self, temp_secrets_dir):
        """Test deleting from all backends."""
        # Set up secrets in both backends
        (Path(temp_secrets_dir) / "shared-secret").write_text("file_val")
        os.environ["SM_DEL_SHARED_SECRET"] = "env_val"

        file_backend = FileSecretsBackend(secrets_dir=temp_secrets_dir)
        env_backend = EnvironmentSecretsBackend(prefix="SM_DEL_")

        manager = SecretsManager(backends=[file_backend, env_backend])

        try:
            result = manager.delete("shared-secret")

            assert result is True
            assert not (Path(temp_secrets_dir) / "shared-secret").exists()
            assert "SM_DEL_SHARED_SECRET" not in os.environ
        finally:
            if "SM_DEL_SHARED_SECRET" in os.environ:
                del os.environ["SM_DEL_SHARED_SECRET"]

    def test_list_from_all_backends(self, temp_secrets_dir):
        """Test listing secrets from all backends."""
        (Path(temp_secrets_dir) / "file-secret").write_text("val")
        os.environ["SM_LIST_ENV_SECRET"] = "val"

        file_backend = FileSecretsBackend(secrets_dir=temp_secrets_dir)
        env_backend = EnvironmentSecretsBackend(prefix="SM_LIST_")

        manager = SecretsManager(backends=[file_backend, env_backend])

        try:
            result = manager.list()

            assert "FileSecretsBackend" in result
            assert "EnvironmentSecretsBackend" in result
            assert "file-secret" in result["FileSecretsBackend"]
            assert "env-secret" in result["EnvironmentSecretsBackend"]
        finally:
            del os.environ["SM_LIST_ENV_SECRET"]


class TestGetSecretFunction:
    """Tests for the get_secret convenience function."""

    def test_get_secret_basic(self):
        """Test basic secret retrieval."""
        os.environ["SANDBOX_SECRET_TEST_KEY"] = "test_value"

        try:
            # This uses the global secrets manager with default backends
            value = get_secret("test-key")
            assert value == "test_value"
        finally:
            del os.environ["SANDBOX_SECRET_TEST_KEY"]

    def test_get_secret_with_default(self):
        """Test secret retrieval with default."""
        value = get_secret("nonexistent-key", default="my_default")
        assert value == "my_default"
