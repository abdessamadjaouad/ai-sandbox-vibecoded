# backend/app/governance/secrets.py
"""
Secrets management service.

Provides a unified interface for managing secrets with support for:
- Environment variables (default, for local development)
- HashiCorp Vault (for production)
- File-based secrets (for Kubernetes secrets)

The implementation is pluggable - in MVP we use environment variables,
but the interface is ready for Vault integration.
"""

import os
from abc import ABC, abstractmethod
from typing import Any

from backend.app.core.config import settings
from backend.app.core.logging import get_logger

logger = get_logger(__name__)


class SecretsBackend(ABC):
    """Abstract base class for secrets backends."""

    @abstractmethod
    def get_secret(self, key: str, default: str | None = None) -> str | None:
        """
        Retrieve a secret by key.

        Args:
            key: Secret key/name
            default: Default value if secret not found

        Returns:
            Secret value or default
        """
        pass

    @abstractmethod
    def set_secret(self, key: str, value: str) -> bool:
        """
        Store a secret (if backend supports it).

        Args:
            key: Secret key/name
            value: Secret value

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def delete_secret(self, key: str) -> bool:
        """
        Delete a secret (if backend supports it).

        Args:
            key: Secret key/name

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def list_secrets(self, prefix: str = "") -> list[str]:
        """
        List available secret keys.

        Args:
            prefix: Optional prefix to filter keys

        Returns:
            List of secret keys
        """
        pass


class EnvironmentSecretsBackend(SecretsBackend):
    """
    Secrets backend using environment variables.

    This is the default backend for local development.
    Secret keys are converted to uppercase with underscores.
    """

    def __init__(self, prefix: str = "SANDBOX_SECRET_"):
        """
        Initialize the environment secrets backend.

        Args:
            prefix: Prefix for all secret environment variables
        """
        self.prefix = prefix

    def _env_key(self, key: str) -> str:
        """Convert a key to environment variable format."""
        return f"{self.prefix}{key.upper().replace('-', '_').replace('.', '_')}"

    def get_secret(self, key: str, default: str | None = None) -> str | None:
        """Get a secret from environment variables."""
        env_key = self._env_key(key)
        value = os.environ.get(env_key, default)

        if value is not None:
            logger.debug("secret_retrieved", key=key, source="environment")
        else:
            logger.debug("secret_not_found", key=key, source="environment")

        return value

    def set_secret(self, key: str, value: str) -> bool:
        """Set a secret in environment variables (in-memory only)."""
        env_key = self._env_key(key)
        os.environ[env_key] = value
        logger.info("secret_set", key=key, source="environment")
        return True

    def delete_secret(self, key: str) -> bool:
        """Delete a secret from environment variables."""
        env_key = self._env_key(key)
        if env_key in os.environ:
            del os.environ[env_key]
            logger.info("secret_deleted", key=key, source="environment")
            return True
        return False

    def list_secrets(self, prefix: str = "") -> list[str]:
        """List all secrets with the configured prefix."""
        full_prefix = f"{self.prefix}{prefix.upper()}"
        keys = []
        for key in os.environ:
            if key.startswith(full_prefix):
                # Strip the prefix to return the logical key
                logical_key = key[len(self.prefix) :].lower().replace("_", "-")
                keys.append(logical_key)
        return keys


class FileSecretsBackend(SecretsBackend):
    """
    Secrets backend using files.

    This is useful for Kubernetes secrets mounted as files.
    Each secret is stored in a separate file.
    """

    def __init__(self, secrets_dir: str = "/run/secrets"):
        """
        Initialize the file secrets backend.

        Args:
            secrets_dir: Directory containing secret files
        """
        self.secrets_dir = secrets_dir

    def _secret_path(self, key: str) -> str:
        """Get the file path for a secret."""
        # Sanitize key to prevent path traversal
        safe_key = key.replace("/", "_").replace("..", "_")
        return os.path.join(self.secrets_dir, safe_key)

    def get_secret(self, key: str, default: str | None = None) -> str | None:
        """Get a secret from a file."""
        path = self._secret_path(key)
        try:
            with open(path, "r") as f:
                value = f.read().strip()
                logger.debug("secret_retrieved", key=key, source="file")
                return value
        except FileNotFoundError:
            logger.debug("secret_not_found", key=key, source="file")
            return default
        except Exception as e:
            logger.error("secret_read_error", key=key, error=str(e))
            return default

    def set_secret(self, key: str, value: str) -> bool:
        """Set a secret in a file."""
        path = self._secret_path(key)
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as f:
                f.write(value)
            # Set restrictive permissions
            os.chmod(path, 0o600)
            logger.info("secret_set", key=key, source="file")
            return True
        except Exception as e:
            logger.error("secret_write_error", key=key, error=str(e))
            return False

    def delete_secret(self, key: str) -> bool:
        """Delete a secret file."""
        path = self._secret_path(key)
        try:
            os.remove(path)
            logger.info("secret_deleted", key=key, source="file")
            return True
        except FileNotFoundError:
            return False
        except Exception as e:
            logger.error("secret_delete_error", key=key, error=str(e))
            return False

    def list_secrets(self, prefix: str = "") -> list[str]:
        """List all secrets in the directory."""
        if not os.path.exists(self.secrets_dir):
            return []

        keys = []
        for filename in os.listdir(self.secrets_dir):
            if filename.startswith(prefix):
                keys.append(filename)
        return keys


class VaultSecretsBackend(SecretsBackend):
    """
    Secrets backend using HashiCorp Vault.

    This is the recommended backend for production.
    Requires VAULT_ADDR and VAULT_TOKEN environment variables.

    Note: This is a stub implementation. For production, use the hvac library.
    """

    def __init__(
        self,
        addr: str | None = None,
        token: str | None = None,
        mount_point: str = "secret",
        path_prefix: str = "ai-sandbox/",
    ):
        """
        Initialize the Vault secrets backend.

        Args:
            addr: Vault server address (defaults to VAULT_ADDR env var)
            token: Vault token (defaults to VAULT_TOKEN env var)
            mount_point: Vault secrets engine mount point
            path_prefix: Prefix for all secret paths
        """
        self.addr = addr or os.environ.get("VAULT_ADDR", "http://localhost:8200")
        self.token = token or os.environ.get("VAULT_TOKEN", "")
        self.mount_point = mount_point
        self.path_prefix = path_prefix

        # Check if we can connect to Vault
        self._available = False
        if self.addr and self.token:
            # In production, we would initialize hvac client here
            logger.info("vault_configured", addr=self.addr, mount_point=mount_point)

    def get_secret(self, key: str, default: str | None = None) -> str | None:
        """Get a secret from Vault."""
        if not self._available:
            logger.warning("vault_not_available", key=key)
            return default

        # Stub: In production, use hvac to read from Vault
        # path = f"{self.path_prefix}{key}"
        # client = hvac.Client(url=self.addr, token=self.token)
        # response = client.secrets.kv.v2.read_secret_version(path=path, mount_point=self.mount_point)
        # return response['data']['data'].get('value', default)

        logger.debug("secret_retrieved", key=key, source="vault")
        return default

    def set_secret(self, key: str, value: str) -> bool:
        """Set a secret in Vault."""
        if not self._available:
            logger.warning("vault_not_available", key=key)
            return False

        # Stub: In production, use hvac to write to Vault
        logger.info("secret_set", key=key, source="vault")
        return True

    def delete_secret(self, key: str) -> bool:
        """Delete a secret from Vault."""
        if not self._available:
            return False

        # Stub: In production, use hvac to delete from Vault
        logger.info("secret_deleted", key=key, source="vault")
        return True

    def list_secrets(self, prefix: str = "") -> list[str]:
        """List secrets from Vault."""
        if not self._available:
            return []

        # Stub: In production, use hvac to list from Vault
        return []


class SecretsManager:
    """
    Unified secrets manager with fallback chain.

    Tries backends in order until a secret is found:
    1. Vault (if configured)
    2. File-based secrets
    3. Environment variables

    Usage:
        secrets = SecretsManager()
        db_password = secrets.get("database-password")
        api_key = secrets.get("openai-api-key", required=True)
    """

    def __init__(
        self,
        backends: list[SecretsBackend] | None = None,
    ):
        """
        Initialize the secrets manager.

        Args:
            backends: List of backends to use (in priority order)
                     Defaults to [Vault, File, Environment]
        """
        if backends is None:
            # Default backend chain
            self.backends: list[SecretsBackend] = [
                VaultSecretsBackend(),
                FileSecretsBackend(),
                EnvironmentSecretsBackend(),
            ]
        else:
            self.backends = backends

        logger.info(
            "secrets_manager_initialized",
            backends=[type(b).__name__ for b in self.backends],
        )

    def get(
        self,
        key: str,
        default: str | None = None,
        required: bool = False,
    ) -> str | None:
        """
        Get a secret, trying each backend in order.

        Args:
            key: Secret key
            default: Default value if not found
            required: If True, raise ValueError when not found

        Returns:
            Secret value

        Raises:
            ValueError: If required=True and secret not found
        """
        for backend in self.backends:
            value = backend.get_secret(key)
            if value is not None:
                return value

        if required and default is None:
            raise ValueError(f"Required secret not found: {key}")

        return default

    def set(self, key: str, value: str, backend_index: int = 0) -> bool:
        """
        Set a secret in a specific backend.

        Args:
            key: Secret key
            value: Secret value
            backend_index: Which backend to use (default: first/primary)

        Returns:
            True if successful
        """
        if backend_index >= len(self.backends):
            return False

        return self.backends[backend_index].set_secret(key, value)

    def delete(self, key: str, backend_index: int | None = None) -> bool:
        """
        Delete a secret from backends.

        Args:
            key: Secret key
            backend_index: Specific backend, or None for all

        Returns:
            True if deleted from at least one backend
        """
        if backend_index is not None:
            if backend_index < len(self.backends):
                return self.backends[backend_index].delete_secret(key)
            return False

        # Delete from all backends
        deleted = False
        for backend in self.backends:
            if backend.delete_secret(key):
                deleted = True
        return deleted

    def list(self, prefix: str = "") -> dict[str, list[str]]:
        """
        List secrets from all backends.

        Args:
            prefix: Optional key prefix filter

        Returns:
            Dict mapping backend name to list of keys
        """
        result = {}
        for backend in self.backends:
            backend_name = type(backend).__name__
            result[backend_name] = backend.list_secrets(prefix)
        return result


# Global secrets manager instance
secrets = SecretsManager()


def get_secret(key: str, default: str | None = None, required: bool = False) -> str | None:
    """
    Convenience function to get a secret.

    Args:
        key: Secret key
        default: Default value if not found
        required: If True, raise ValueError when not found

    Returns:
        Secret value
    """
    return secrets.get(key, default=default, required=required)
