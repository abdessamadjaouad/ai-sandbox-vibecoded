# tests/unit/test_data_layer/test_storage.py
from unittest.mock import MagicMock, patch

import pytest


class TestStorageClient:
    @patch("backend.app.data_layer.storage.Minio")
    def test_upload_bytes_calls_put_object(self, MockMinio):
        """Upload bytes should call MinIO put_object."""
        mock_client = MagicMock()
        mock_client.bucket_exists.return_value = True
        MockMinio.return_value = mock_client

        from backend.app.data_layer.storage import StorageClient

        storage = StorageClient(
            endpoint="localhost:9000",
            access_key="test",
            secret_key="test",
            bucket_name="test-bucket",
        )

        result = storage.upload_bytes("test/path.txt", b"content", "text/plain")

        assert mock_client.put_object.called
        assert "test-bucket/test/path.txt" == result

    @patch("backend.app.data_layer.storage.Minio")
    def test_download_file_returns_bytes(self, MockMinio):
        """Download file should return file contents as bytes."""
        mock_client = MagicMock()
        mock_client.bucket_exists.return_value = True
        mock_response = MagicMock()
        mock_response.read.return_value = b"file content"
        mock_client.get_object.return_value = mock_response
        MockMinio.return_value = mock_client

        from backend.app.data_layer.storage import StorageClient

        storage = StorageClient(
            endpoint="localhost:9000",
            access_key="test",
            secret_key="test",
            bucket_name="test-bucket",
        )

        result = storage.download_file("test/path.txt")

        assert result == b"file content"

    @patch("backend.app.data_layer.storage.Minio")
    def test_file_exists_returns_true_when_exists(self, MockMinio):
        """File exists should return True when file exists."""
        mock_client = MagicMock()
        mock_client.bucket_exists.return_value = True
        mock_client.stat_object.return_value = MagicMock()
        MockMinio.return_value = mock_client

        from backend.app.data_layer.storage import StorageClient

        storage = StorageClient(
            endpoint="localhost:9000",
            access_key="test",
            secret_key="test",
            bucket_name="test-bucket",
        )

        assert storage.file_exists("test/path.txt") is True

    @patch("backend.app.data_layer.storage.Minio")
    def test_file_exists_returns_false_when_not_exists(self, MockMinio):
        """File exists should return False when file doesn't exist."""
        from minio.error import S3Error

        mock_client = MagicMock()
        mock_client.bucket_exists.return_value = True
        mock_client.stat_object.side_effect = S3Error("NoSuchKey", "NoSuchKey", None, None, None, None)
        MockMinio.return_value = mock_client

        from backend.app.data_layer.storage import StorageClient

        storage = StorageClient(
            endpoint="localhost:9000",
            access_key="test",
            secret_key="test",
            bucket_name="test-bucket",
        )

        assert storage.file_exists("nonexistent.txt") is False

    @patch("backend.app.data_layer.storage.Minio")
    def test_creates_bucket_if_not_exists(self, MockMinio):
        """Storage client should create bucket if it doesn't exist."""
        mock_client = MagicMock()
        mock_client.bucket_exists.return_value = False
        MockMinio.return_value = mock_client

        from backend.app.data_layer.storage import StorageClient

        StorageClient(
            endpoint="localhost:9000",
            access_key="test",
            secret_key="test",
            bucket_name="new-bucket",
        )

        mock_client.make_bucket.assert_called_once_with("new-bucket")
