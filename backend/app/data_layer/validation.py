# backend/app/data_layer/validation.py
from typing import Any

import pandas as pd

from backend.app.core.logging import get_logger
from backend.app.models.dataset import ValidationReport

logger = get_logger(__name__)


class ValidationError(Exception):
    """Raised when dataset validation fails critically."""

    pass


class DatasetValidationService:
    """Service for validating dataset quality and integrity."""

    DEFAULT_NULL_THRESHOLD = 0.5
    DEFAULT_DUPLICATE_THRESHOLD = 0.1

    def __init__(
        self,
        null_threshold: float = DEFAULT_NULL_THRESHOLD,
        duplicate_threshold: float = DEFAULT_DUPLICATE_THRESHOLD,
    ) -> None:
        """Initialize validation service.

        Args:
            null_threshold: Maximum allowed null ratio per column (0.0-1.0).
            duplicate_threshold: Maximum allowed duplicate row ratio (0.0-1.0).
        """
        self.null_threshold = null_threshold
        self.duplicate_threshold = duplicate_threshold

    def validate(self, df: pd.DataFrame) -> ValidationReport:
        """Validate a DataFrame and return a validation report.

        Args:
            df: Pandas DataFrame to validate.

        Returns:
            ValidationReport with validation results.
        """
        issues: list[str] = []
        warnings: list[str] = []

        total_rows = len(df)
        total_columns = len(df.columns)

        null_counts = df.isnull().sum().to_dict()
        null_percentages = {
            col: (count / total_rows * 100) if total_rows > 0 else 0 for col, count in null_counts.items()
        }

        for col, pct in null_percentages.items():
            if pct > self.null_threshold * 100:
                issues.append(f"Column '{col}' has {pct:.1f}% null values (threshold: {self.null_threshold * 100}%)")
            elif pct > 10:
                warnings.append(f"Column '{col}' has {pct:.1f}% null values")

        dtypes = {col: str(dtype) for col, dtype in df.dtypes.items()}

        duplicate_rows = int(df.duplicated().sum())
        duplicate_ratio = duplicate_rows / total_rows if total_rows > 0 else 0

        if duplicate_ratio > self.duplicate_threshold:
            issues.append(
                f"Dataset has {duplicate_ratio * 100:.1f}% duplicate rows (threshold: {self.duplicate_threshold * 100}%)"
            )
        elif duplicate_rows > 0:
            warnings.append(f"Dataset has {duplicate_rows} duplicate rows ({duplicate_ratio * 100:.1f}%)")

        if total_rows == 0:
            issues.append("Dataset is empty (0 rows)")

        if total_columns == 0:
            issues.append("Dataset has no columns")

        self._validate_column_names(df, issues, warnings)
        self._validate_data_types(df, issues, warnings)

        is_valid = len(issues) == 0

        report = ValidationReport(
            is_valid=is_valid,
            total_rows=total_rows,
            total_columns=total_columns,
            null_counts={k: int(v) for k, v in null_counts.items()},
            null_percentages={k: round(v, 2) for k, v in null_percentages.items()},
            dtypes=dtypes,
            duplicate_rows=duplicate_rows,
            issues=issues,
            warnings=warnings,
        )

        logger.info(
            "dataset_validated",
            is_valid=is_valid,
            rows=total_rows,
            columns=total_columns,
            issues_count=len(issues),
            warnings_count=len(warnings),
        )

        return report

    def _validate_column_names(
        self,
        df: pd.DataFrame,
        issues: list[str],
        warnings: list[str],
    ) -> None:
        """Validate column naming conventions.

        Args:
            df: DataFrame to validate.
            issues: List to append critical issues.
            warnings: List to append warnings.
        """
        for col in df.columns:
            if not isinstance(col, str):
                warnings.append(f"Column name '{col}' is not a string")
                continue

            if col.strip() != col:
                warnings.append(f"Column '{col}' has leading/trailing whitespace")

            if col == "":
                issues.append("Dataset has empty column name")

        duplicates = df.columns[df.columns.duplicated()].tolist()
        if duplicates:
            issues.append(f"Duplicate column names found: {duplicates}")

    def _validate_data_types(
        self,
        df: pd.DataFrame,
        issues: list[str],
        warnings: list[str],
    ) -> None:
        """Validate data type consistency.

        Args:
            df: DataFrame to validate.
            issues: List to append critical issues.
            warnings: List to append warnings.
        """
        for col in df.columns:
            try:
                col_series = df[col]
                # Handle duplicate columns by checking if we got a DataFrame
                if isinstance(col_series, pd.DataFrame):
                    continue  # Skip duplicate columns, already flagged in column validation
                if col_series.dtype == "object":
                    non_null = col_series.dropna()
                    if len(non_null) > 0:
                        types = non_null.apply(type).unique()
                        if len(types) > 1:
                            type_names = [t.__name__ for t in types]
                            warnings.append(f"Column '{col}' has mixed types: {type_names}")
            except Exception:
                continue  # Skip problematic columns

    def get_column_statistics(self, df: pd.DataFrame) -> dict[str, dict[str, Any]]:
        """Calculate detailed statistics for each column.

        Args:
            df: DataFrame to analyze.

        Returns:
            Dict mapping column names to their statistics.
        """
        stats = {}

        for col in df.columns:
            col_stats: dict[str, Any] = {
                "dtype": str(df[col].dtype),
                "null_count": int(df[col].isnull().sum()),
                "unique_count": int(df[col].nunique()),
            }

            if pd.api.types.is_numeric_dtype(df[col]):
                col_stats.update(
                    {
                        "min": float(df[col].min()) if not df[col].isnull().all() else None,
                        "max": float(df[col].max()) if not df[col].isnull().all() else None,
                        "mean": float(df[col].mean()) if not df[col].isnull().all() else None,
                        "std": float(df[col].std()) if not df[col].isnull().all() else None,
                        "median": float(df[col].median()) if not df[col].isnull().all() else None,
                    }
                )
            elif df[col].dtype == "object":
                value_counts = df[col].value_counts()
                col_stats["top_values"] = value_counts.head(5).to_dict()
                col_stats["avg_length"] = (
                    float(df[col].dropna().astype(str).str.len().mean()) if len(df[col].dropna()) > 0 else 0
                )

            stats[col] = col_stats

        return stats
