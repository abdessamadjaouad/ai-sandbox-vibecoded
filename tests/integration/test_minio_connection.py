# tests/integration/test_minio_connection.py
from unittest.mock import MagicMock, patch

import pytest


def test_minio_config_is_set():
    """MinIO configuration should be present."""
    from backend.app.core.config import settings

    assert settings.minio_endpoint is not None
    assert settings.minio_access_key is not None
    assert settings.minio_secret_key is not None
    assert settings.minio_bucket_name == "sandbox"


def test_minio_client_can_be_instantiated():
    """MinIO client should be instantiable with config settings."""
    from backend.app.core.config import settings

    with patch("minio.Minio") as MockMinio:
        mock_client = MagicMock()
        MockMinio.return_value = mock_client

        from minio import Minio

        client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )

        MockMinio.assert_called_once_with(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )
