# tests/unit/test_data_layer/test_versioning.py
from unittest.mock import MagicMock
from uuid import uuid4

import pandas as pd
import pytest

from backend.app.data_layer.versioning import DatasetVersioningService, VersioningError


@pytest.fixture
def mock_storage():
    """Mock storage client."""
    storage = MagicMock()
    storage.upload_bytes = MagicMock()
    return storage


@pytest.fixture
def versioning_service(mock_storage):
    """Versioning service with mock storage."""
    return DatasetVersioningService(mock_storage)


@pytest.fixture
def sample_dataframe():
    """Sample DataFrame for testing."""
    return pd.DataFrame(
        {
            "feature1": range(100),
            "feature2": [f"text_{i}" for i in range(100)],
            "label": [i % 2 for i in range(100)],
        }
    )


class TestDatasetVersioningService:
    def test_create_version_default_split(self, versioning_service, sample_dataframe):
        """Default 70/15/15 split should work."""
        result = versioning_service.create_version(
            df=sample_dataframe,
            dataset_id=uuid4(),
            version=1,
        )

        assert result["train_rows"] == 70
        assert result["val_rows"] == 15
        assert result["test_rows"] == 15
        assert result["config_hash"] is not None

    def test_create_version_custom_split(self, versioning_service, sample_dataframe):
        """Custom split ratios should work."""
        result = versioning_service.create_version(
            df=sample_dataframe,
            dataset_id=uuid4(),
            version=1,
            train_ratio=0.8,
            val_ratio=0.1,
            test_ratio=0.1,
        )

        assert result["train_rows"] == 80
        assert result["val_rows"] == 10
        assert result["test_rows"] == 10

    def test_invalid_split_ratios_raises_error(self, versioning_service, sample_dataframe):
        """Split ratios not summing to 1.0 should raise error."""
        with pytest.raises(VersioningError, match="must sum to 1.0"):
            versioning_service.create_version(
                df=sample_dataframe,
                dataset_id=uuid4(),
                version=1,
                train_ratio=0.5,
                val_ratio=0.2,
                test_ratio=0.2,  # Sum = 0.9
            )

    def test_small_dataset_raises_error(self, versioning_service):
        """Dataset with fewer than 10 rows should raise error."""
        small_df = pd.DataFrame({"col": range(5)})

        with pytest.raises(VersioningError, match="too small"):
            versioning_service.create_version(
                df=small_df,
                dataset_id=uuid4(),
                version=1,
            )

    def test_reproducible_split_with_seed(self, versioning_service, sample_dataframe):
        """Same seed should produce same split."""
        dataset_id = uuid4()

        result1 = versioning_service.create_version(
            df=sample_dataframe,
            dataset_id=dataset_id,
            version=1,
            random_seed=42,
        )

        result2 = versioning_service.create_version(
            df=sample_dataframe,
            dataset_id=dataset_id,
            version=2,
            random_seed=42,
        )

        assert result1["config_hash"] == result2["config_hash"]

    def test_train_only_split(self, versioning_service, sample_dataframe):
        """Split with only training data should work."""
        result = versioning_service.create_version(
            df=sample_dataframe,
            dataset_id=uuid4(),
            version=1,
            train_ratio=1.0,
            val_ratio=0.0,
            test_ratio=0.0,
        )

        assert result["train_rows"] == 100
        assert result["val_rows"] is None
        assert result["test_rows"] is None

    def test_config_hash_deterministic(self, versioning_service):
        """Config hash should be deterministic."""
        hash1 = versioning_service._compute_config_hash(
            {
                "train_ratio": 0.7,
                "val_ratio": 0.15,
                "test_ratio": 0.15,
            }
        )

        hash2 = versioning_service._compute_config_hash(
            {
                "train_ratio": 0.7,
                "val_ratio": 0.15,
                "test_ratio": 0.15,
            }
        )

        assert hash1 == hash2
