# tests/unit/test_config.py
import os
from unittest.mock import patch

import pytest


def test_settings_loads_defaults():
    """Verify Settings loads with default values when no env vars set."""
    with patch.dict(os.environ, {}, clear=True):
        from backend.app.core.config import Settings

        s = Settings()
        assert s.app_name == "AI Sandbox"
        assert s.app_version == "0.1.0"
        assert s.debug is False
        assert s.log_level == "info"
        assert s.default_random_seed == 42


def test_settings_respects_env_vars():
    """Verify Settings reads from environment variables."""
    env_vars = {
        "APP_NAME": "Test Sandbox",
        "DEBUG": "true",
        "LOG_LEVEL": "debug",
        "DEFAULT_RANDOM_SEED": "123",
    }
    with patch.dict(os.environ, env_vars, clear=False):
        from backend.app.core.config import Settings

        s = Settings()
        assert s.app_name == "Test Sandbox"
        assert s.debug is True
        assert s.log_level == "debug"
        assert s.default_random_seed == 123


def test_settings_database_url_format():
    """Verify database URL follows asyncpg format."""
    from backend.app.core.config import settings

    assert "postgresql+asyncpg://" in settings.database_url


def test_settings_minio_defaults():
    """Verify MinIO settings have sane defaults."""
    from backend.app.core.config import settings

    assert settings.minio_endpoint is not None
    assert settings.minio_bucket_name == "sandbox"
    assert settings.minio_secure is False
