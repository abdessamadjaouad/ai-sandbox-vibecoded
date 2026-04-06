# backend/app/data_layer/storage.py
import io
from typing import BinaryIO

from minio import Minio
from minio.error import S3Error

from backend.app.core.config import settings
from backend.app.core.logging import get_logger

logger = get_logger(__name__)


class StorageClient:
    """MinIO storage client wrapper for object storage operations."""

    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket_name: str,
        secure: bool = False,
    ) -> None:
        """Initialize MinIO client.

        Args:
            endpoint: MinIO server endpoint (host:port).
            access_key: MinIO access key.
            secret_key: MinIO secret key.
            bucket_name: Default bucket name.
            secure: Use HTTPS if True.
        """
        self.client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
        )
        self.bucket_name = bucket_name
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self) -> None:
        """Create the bucket if it doesn't exist."""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info("bucket_created", bucket=self.bucket_name)
        except S3Error as e:
            logger.error("bucket_creation_failed", bucket=self.bucket_name, error=str(e))
            raise

    def upload_file(
        self,
        object_name: str,
        data: BinaryIO,
        length: int,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Upload a file to MinIO.

        Args:
            object_name: Name/path of the object in the bucket.
            data: File-like object containing the data.
            length: Size of the data in bytes.
            content_type: MIME type of the file.

        Returns:
            The full path (bucket/object_name) of the uploaded file.

        Raises:
            S3Error: If upload fails.
        """
        try:
            self.client.put_object(
                self.bucket_name,
                object_name,
                data,
                length,
                content_type=content_type,
            )
            path = f"{self.bucket_name}/{object_name}"
            logger.info("file_uploaded", path=path, size=length)
            return path
        except S3Error as e:
            logger.error("file_upload_failed", object_name=object_name, error=str(e))
            raise

    def upload_bytes(
        self,
        object_name: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Upload bytes to MinIO.

        Args:
            object_name: Name/path of the object in the bucket.
            data: Bytes to upload.
            content_type: MIME type of the file.

        Returns:
            The full path (bucket/object_name) of the uploaded file.
        """
        return self.upload_file(
            object_name,
            io.BytesIO(data),
            len(data),
            content_type,
        )

    def download_file(self, object_name: str) -> bytes:
        """Download a file from MinIO.

        Args:
            object_name: Name/path of the object in the bucket.

        Returns:
            The file contents as bytes.

        Raises:
            S3Error: If download fails.
        """
        try:
            response = self.client.get_object(self.bucket_name, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            logger.info("file_downloaded", object_name=object_name, size=len(data))
            return data
        except S3Error as e:
            logger.error("file_download_failed", object_name=object_name, error=str(e))
            raise

    def delete_file(self, object_name: str) -> None:
        """Delete a file from MinIO.

        Args:
            object_name: Name/path of the object in the bucket.

        Raises:
            S3Error: If deletion fails.
        """
        try:
            self.client.remove_object(self.bucket_name, object_name)
            logger.info("file_deleted", object_name=object_name)
        except S3Error as e:
            logger.error("file_delete_failed", object_name=object_name, error=str(e))
            raise

    def file_exists(self, object_name: str) -> bool:
        """Check if a file exists in MinIO.

        Args:
            object_name: Name/path of the object in the bucket.

        Returns:
            True if file exists, False otherwise.
        """
        try:
            self.client.stat_object(self.bucket_name, object_name)
            return True
        except S3Error:
            return False

    def list_files(self, prefix: str = "") -> list[str]:
        """List files in the bucket with optional prefix filter.

        Args:
            prefix: Filter files by this prefix.

        Returns:
            List of object names matching the prefix.
        """
        objects = self.client.list_objects(self.bucket_name, prefix=prefix, recursive=True)
        return [obj.object_name for obj in objects]


_storage_client: StorageClient | None = None


def get_storage_client() -> StorageClient:
    """Get or create the singleton storage client.

    Returns:
        StorageClient instance configured from settings.
    """
    global _storage_client
    if _storage_client is None:
        _storage_client = StorageClient(
            endpoint=settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            bucket_name=settings.minio_bucket_name,
            secure=settings.minio_secure,
        )
    return _storage_client
