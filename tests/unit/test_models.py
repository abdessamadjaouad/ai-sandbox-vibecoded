# tests/unit/test_models.py
import uuid
from datetime import datetime

import pytest
from pydantic import ValidationError

from backend.app.models.dataset import (
    DatasetCreate,
    DatasetRead,
    DatasetStatus,
    DatasetType,
    DatasetVersionCreate,
    ValidationReport,
)


class TestDatasetSchemas:
    def test_dataset_create_valid(self):
        """Valid DatasetCreate should pass validation."""
        data = DatasetCreate(
            name="Test Dataset",
            description="A test dataset",
            dataset_type=DatasetType.TABULAR,
        )
        assert data.name == "Test Dataset"
        assert data.dataset_type == DatasetType.TABULAR

    def test_dataset_create_empty_name_fails(self):
        """Empty name should fail validation."""
        with pytest.raises(ValidationError):
            DatasetCreate(name="", dataset_type=DatasetType.TABULAR)

    def test_dataset_read_from_attributes(self):
        """DatasetRead should work with from_attributes."""

        class MockDataset:
            id = uuid.uuid4()
            name = "Test"
            description = None
            dataset_type = DatasetType.TABULAR
            status = DatasetStatus.VALIDATED
            file_path = "test/path"
            file_size_bytes = 1000
            file_format = "csv"
            row_count = 100
            column_count = 5
            schema_info = {}
            validation_report = {}
            created_at = datetime.now()
            updated_at = datetime.now()

        result = DatasetRead.model_validate(MockDataset())
        assert result.name == "Test"

    def test_dataset_version_create_valid_ratios(self):
        """Valid split ratios should pass."""
        config = DatasetVersionCreate(
            train_ratio=0.7,
            val_ratio=0.15,
            test_ratio=0.15,
        )
        assert config.train_ratio == 0.7

    def test_dataset_version_create_invalid_ratio_fails(self):
        """Ratio outside bounds should fail."""
        with pytest.raises(ValidationError):
            DatasetVersionCreate(train_ratio=0.05)  # Below 0.1

    def test_validation_report_structure(self):
        """ValidationReport should accept valid structure."""
        report = ValidationReport(
            is_valid=True,
            total_rows=100,
            total_columns=5,
            null_counts={"col1": 0, "col2": 5},
            null_percentages={"col1": 0.0, "col2": 5.0},
            dtypes={"col1": "int64", "col2": "object"},
            duplicate_rows=0,
            issues=[],
            warnings=["Minor warning"],
        )
        assert report.is_valid is True
        assert len(report.warnings) == 1


class TestDatasetEnums:
    def test_dataset_status_values(self):
        """DatasetStatus should have expected values."""
        assert DatasetStatus.PENDING == "pending"
        assert DatasetStatus.VALIDATED == "validated"
        assert DatasetStatus.INDEXED == "indexed"

    def test_dataset_type_values(self):
        """DatasetType should have expected values."""
        assert DatasetType.TABULAR == "tabular"
        assert DatasetType.TEXT == "text"
        assert DatasetType.MIXED == "mixed"
