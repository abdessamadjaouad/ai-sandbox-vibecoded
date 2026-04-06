# backend/app/data_layer/versioning.py
import hashlib
import io
import uuid
from typing import Any

import pandas as pd
from sklearn.model_selection import train_test_split

from backend.app.core.config import settings
from backend.app.core.logging import get_logger
from backend.app.data_layer.storage import StorageClient

logger = get_logger(__name__)


class VersioningError(Exception):
    """Raised when dataset versioning fails."""

    pass


class DatasetVersioningService:
    """Service for creating versioned train/val/test splits."""

    def __init__(self, storage_client: StorageClient) -> None:
        """Initialize versioning service.

        Args:
            storage_client: MinIO storage client for file storage.
        """
        self.storage = storage_client

    def create_version(
        self,
        df: pd.DataFrame,
        dataset_id: uuid.UUID,
        version: int,
        train_ratio: float = 0.7,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15,
        random_seed: int | None = None,
        stratify_column: str | None = None,
    ) -> dict[str, Any]:
        """Create a new version with train/val/test splits.

        Args:
            df: Source DataFrame to split.
            dataset_id: UUID of the parent dataset.
            version: Version number.
            train_ratio: Ratio of data for training (0.0-1.0).
            val_ratio: Ratio of data for validation (0.0-1.0).
            test_ratio: Ratio of data for testing (0.0-1.0).
            random_seed: Random seed for reproducibility.
            stratify_column: Column name for stratified splitting.

        Returns:
            Dict with split paths, row counts, config hash, and split config.

        Raises:
            VersioningError: If ratios are invalid or splitting fails.
        """
        if random_seed is None:
            random_seed = settings.default_random_seed

        total_ratio = train_ratio + val_ratio + test_ratio
        if abs(total_ratio - 1.0) > 0.01:
            raise VersioningError(f"Split ratios must sum to 1.0, got {total_ratio}")

        if len(df) < 10:
            raise VersioningError(f"Dataset too small for splitting: {len(df)} rows (minimum 10)")

        split_config = {
            "train_ratio": train_ratio,
            "val_ratio": val_ratio,
            "test_ratio": test_ratio,
            "random_seed": random_seed,
            "stratify_column": stratify_column,
        }
        config_hash = self._compute_config_hash(split_config)

        stratify = df[stratify_column] if stratify_column and stratify_column in df.columns else None

        # Handle 100% training case (no split needed)
        if train_ratio >= 0.99:
            train_df = df.copy()
            temp_df = pd.DataFrame()
        else:
            train_df, temp_df = train_test_split(
                df,
                train_size=train_ratio,
                random_state=random_seed,
                stratify=stratify,
            )

        val_df = None
        test_df = None
        val_path = None
        test_path = None
        val_rows = None
        test_rows = None

        if len(temp_df) > 0:
            if val_ratio > 0 and test_ratio > 0:
                relative_test_ratio = test_ratio / (val_ratio + test_ratio)
                stratify_temp = (
                    temp_df[stratify_column] if stratify_column and stratify_column in temp_df.columns else None
                )

                val_df, test_df = train_test_split(
                    temp_df,
                    test_size=relative_test_ratio,
                    random_state=random_seed,
                    stratify=stratify_temp,
                )
            elif val_ratio > 0:
                val_df = temp_df
            elif test_ratio > 0:
                test_df = temp_df

        base_path = f"datasets/{dataset_id}/v{version}"

        train_path = f"{base_path}/train.parquet"
        self._save_split(train_df, train_path)

        if val_df is not None and len(val_df) > 0:
            val_path = f"{base_path}/val.parquet"
            self._save_split(val_df, val_path)
            val_rows = len(val_df)

        if test_df is not None and len(test_df) > 0:
            test_path = f"{base_path}/test.parquet"
            self._save_split(test_df, test_path)
            test_rows = len(test_df)

        logger.info(
            "dataset_version_created",
            dataset_id=str(dataset_id),
            version=version,
            train_rows=len(train_df),
            val_rows=val_rows,
            test_rows=test_rows,
            config_hash=config_hash,
        )

        return {
            "split_config": split_config,
            "train_path": train_path,
            "val_path": val_path,
            "test_path": test_path,
            "train_rows": len(train_df),
            "val_rows": val_rows,
            "test_rows": test_rows,
            "random_seed": random_seed,
            "config_hash": config_hash,
        }

    def _save_split(self, df: pd.DataFrame, path: str) -> None:
        """Save a DataFrame split to storage as parquet.

        Args:
            df: DataFrame to save.
            path: Storage path.
        """
        buffer = io.BytesIO()
        df.to_parquet(buffer, index=False)
        buffer.seek(0)
        self.storage.upload_bytes(path, buffer.read(), "application/parquet")

    def _compute_config_hash(self, config: dict) -> str:
        """Compute a deterministic hash of the split configuration.

        Args:
            config: Split configuration dict.

        Returns:
            SHA-256 hash string (first 16 chars).
        """
        config_str = str(sorted(config.items()))
        return hashlib.sha256(config_str.encode()).hexdigest()[:16]

    def load_split(self, path: str) -> pd.DataFrame:
        """Load a split DataFrame from storage.

        Args:
            path: Storage path to the parquet file.

        Returns:
            Loaded DataFrame.
        """
        content = self.storage.download_file(path)
        return pd.read_parquet(io.BytesIO(content))
