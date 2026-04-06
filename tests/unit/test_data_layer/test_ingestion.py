# tests/unit/test_data_layer/test_ingestion.py
import io
from unittest.mock import MagicMock

import pandas as pd
import pytest

from backend.app.data_layer.ingestion import DatasetIngestionService, IngestionError
from backend.app.models.dataset import DatasetType


@pytest.fixture
def mock_storage():
    """Mock storage client."""
    storage = MagicMock()
    storage.upload_bytes = MagicMock(return_value="datasets/test/raw/test.csv")
    storage.download_file = MagicMock()
    return storage


@pytest.fixture
def ingestion_service(mock_storage):
    """Ingestion service with mock storage."""
    return DatasetIngestionService(mock_storage)


class TestDatasetIngestionService:
    def test_parse_csv_to_dataframe(self, ingestion_service):
        """CSV content should be parsed to DataFrame."""
        csv_content = b"col1,col2,col3\n1,2,3\n4,5,6\n"
        df = ingestion_service._parse_to_dataframe(csv_content, ".csv")

        assert len(df) == 2
        assert list(df.columns) == ["col1", "col2", "col3"]

    def test_parse_json_to_dataframe(self, ingestion_service):
        """JSON content should be parsed to DataFrame."""
        json_content = b'[{"col1": 1, "col2": 2}, {"col1": 3, "col2": 4}]'
        df = ingestion_service._parse_to_dataframe(json_content, ".json")

        assert len(df) == 2
        assert "col1" in df.columns

    def test_unsupported_format_raises_error(self, ingestion_service):
        """Unsupported file format should raise IngestionError."""
        file_data = io.BytesIO(b"test content")

        with pytest.raises(IngestionError, match="Unsupported file format"):
            ingestion_service.ingest_file(file_data, "test.unsupported", MagicMock())

    def test_extract_schema(self, ingestion_service):
        """Schema should be extracted from DataFrame."""
        df = pd.DataFrame(
            {
                "int_col": [1, 2, 3],
                "str_col": ["a", "b", "c"],
                "float_col": [1.1, 2.2, 3.3],
            }
        )

        schema = ingestion_service._extract_schema(df)

        assert "columns" in schema
        assert "dtypes" in schema
        assert len(schema["columns"]) == 3
        assert "int64" in schema["dtypes"]["int_col"]

    def test_detect_dataset_type_tabular(self, ingestion_service):
        """Numeric-heavy schema should be detected as TABULAR."""
        schema = {"dtypes": {"col1": "int64", "col2": "float64", "col3": "int32"}}
        result = ingestion_service.detect_dataset_type(schema)
        assert result == DatasetType.TABULAR

    def test_detect_dataset_type_text(self, ingestion_service):
        """String-heavy schema should be detected as TEXT."""
        schema = {"dtypes": {"col1": "object", "col2": "string", "col3": "object"}}
        result = ingestion_service.detect_dataset_type(schema)
        assert result == DatasetType.TEXT

    def test_detect_dataset_type_mixed(self, ingestion_service):
        """Mixed schema should be detected as MIXED."""
        schema = {"dtypes": {"col1": "int64", "col2": "object", "col3": "float64", "col4": "string"}}
        result = ingestion_service.detect_dataset_type(schema)
        assert result == DatasetType.MIXED
