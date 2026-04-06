# backend/app/data_layer/ingestion.py
import io
import json
import uuid
from pathlib import Path
from typing import BinaryIO

import pandas as pd

from backend.app.core.logging import get_logger
from backend.app.data_layer.storage import StorageClient
from backend.app.models.dataset import DatasetType

logger = get_logger(__name__)


class IngestionError(Exception):
    """Raised when dataset ingestion fails."""

    pass


class DatasetIngestionService:
    """Service for ingesting datasets from various file formats."""

    SUPPORTED_FORMATS = {
        ".csv": "text/csv",
        ".json": "application/json",
        ".jsonl": "application/jsonlines",
        ".parquet": "application/parquet",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".xls": "application/vnd.ms-excel",
    }

    def __init__(self, storage_client: StorageClient) -> None:
        """Initialize ingestion service.

        Args:
            storage_client: MinIO storage client for file storage.
        """
        self.storage = storage_client

    def ingest_file(
        self,
        file_data: BinaryIO,
        filename: str,
        dataset_id: uuid.UUID,
    ) -> dict:
        """Ingest a file and store it in object storage.

        Args:
            file_data: File-like object containing the data.
            filename: Original filename.
            dataset_id: UUID of the dataset record.

        Returns:
            Dict with file_path, file_size_bytes, file_format, row_count, column_count, schema_info.

        Raises:
            IngestionError: If file format is unsupported or parsing fails.
        """
        ext = Path(filename).suffix.lower()
        if ext not in self.SUPPORTED_FORMATS:
            raise IngestionError(f"Unsupported file format: {ext}. Supported: {list(self.SUPPORTED_FORMATS.keys())}")

        content = file_data.read()
        file_size = len(content)

        object_name = f"datasets/{dataset_id}/raw/{filename}"
        content_type = self.SUPPORTED_FORMATS[ext]

        self.storage.upload_bytes(object_name, content, content_type)

        df = self._parse_to_dataframe(content, ext)
        schema_info = self._extract_schema(df)

        logger.info(
            "dataset_ingested",
            dataset_id=str(dataset_id),
            filename=filename,
            rows=len(df),
            columns=len(df.columns),
        )

        return {
            "file_path": object_name,
            "file_size_bytes": file_size,
            "file_format": ext.lstrip("."),
            "row_count": len(df),
            "column_count": len(df.columns),
            "schema_info": schema_info,
        }

    def _parse_to_dataframe(self, content: bytes, ext: str) -> pd.DataFrame:
        """Parse file content to pandas DataFrame.

        Args:
            content: Raw file bytes.
            ext: File extension.

        Returns:
            Parsed DataFrame.

        Raises:
            IngestionError: If parsing fails.
        """
        try:
            buffer = io.BytesIO(content)

            if ext == ".csv":
                return pd.read_csv(buffer)
            elif ext == ".json":
                return pd.read_json(buffer)
            elif ext == ".jsonl":
                return pd.read_json(buffer, lines=True)
            elif ext == ".parquet":
                return pd.read_parquet(buffer)
            elif ext in (".xlsx", ".xls"):
                return pd.read_excel(buffer)
            else:
                raise IngestionError(f"Parser not implemented for {ext}")
        except Exception as e:
            logger.error("parse_failed", ext=ext, error=str(e))
            raise IngestionError(f"Failed to parse file: {e}") from e

    def _extract_schema(self, df: pd.DataFrame) -> dict:
        """Extract schema information from DataFrame.

        Args:
            df: Pandas DataFrame.

        Returns:
            Dict with column names, types, and basic stats.
        """
        schema = {
            "columns": [],
            "dtypes": {},
            "nullable": {},
        }

        for col in df.columns:
            dtype_str = str(df[col].dtype)
            null_count = int(df[col].isnull().sum())

            schema["columns"].append(col)
            schema["dtypes"][col] = dtype_str
            schema["nullable"][col] = null_count > 0

        return schema

    def detect_dataset_type(self, schema_info: dict) -> DatasetType:
        """Detect the dataset type based on column dtypes.

        Args:
            schema_info: Schema information dict.

        Returns:
            DatasetType enum value.
        """
        dtypes = schema_info.get("dtypes", {})

        text_types = sum(1 for dt in dtypes.values() if "object" in dt or "string" in dt)
        numeric_types = sum(1 for dt in dtypes.values() if "int" in dt or "float" in dt)
        total = len(dtypes)

        if total == 0:
            return DatasetType.TABULAR

        text_ratio = text_types / total
        numeric_ratio = numeric_types / total

        if text_ratio > 0.7:
            return DatasetType.TEXT
        elif numeric_ratio > 0.7:
            return DatasetType.TABULAR
        else:
            return DatasetType.MIXED

    def load_dataframe(self, file_path: str, file_format: str) -> pd.DataFrame:
        """Load a DataFrame from storage.

        Args:
            file_path: Path to file in storage.
            file_format: File format (csv, json, etc.).

        Returns:
            Loaded DataFrame.
        """
        content = self.storage.download_file(file_path)
        return self._parse_to_dataframe(content, f".{file_format}")
