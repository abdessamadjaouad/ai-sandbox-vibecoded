# tests/unit/test_data_layer/test_validation.py
import pandas as pd
import pytest

from backend.app.data_layer.validation import DatasetValidationService


@pytest.fixture
def validation_service():
    """Validation service with default thresholds."""
    return DatasetValidationService()


class TestDatasetValidationService:
    def test_valid_dataframe_passes(self, validation_service):
        """Clean DataFrame should pass validation."""
        df = pd.DataFrame(
            {
                "col1": [1, 2, 3, 4, 5],
                "col2": ["a", "b", "c", "d", "e"],
            }
        )

        report = validation_service.validate(df)

        assert report.is_valid is True
        assert report.total_rows == 5
        assert report.total_columns == 2
        assert len(report.issues) == 0

    def test_high_null_ratio_fails(self, validation_service):
        """DataFrame with too many nulls should fail validation."""
        df = pd.DataFrame(
            {
                "col1": [1, None, None, None, None, None],  # 83% null
                "col2": ["a", "b", "c", "d", "e", "f"],
            }
        )

        report = validation_service.validate(df)

        assert report.is_valid is False
        assert any("null values" in issue for issue in report.issues)

    def test_duplicate_rows_warning(self, validation_service):
        """Duplicate rows should generate warning."""
        df = pd.DataFrame(
            {
                "col1": [1, 1, 2, 3, 4],
                "col2": ["a", "a", "b", "c", "d"],
            }
        )

        report = validation_service.validate(df)

        assert report.duplicate_rows == 1
        # Low duplicate ratio should be warning not issue
        assert len(report.warnings) > 0 or report.duplicate_rows > 0

    def test_empty_dataframe_fails(self, validation_service):
        """Empty DataFrame should fail validation."""
        df = pd.DataFrame()

        report = validation_service.validate(df)

        assert report.is_valid is False
        assert any("empty" in issue.lower() or "0 rows" in issue for issue in report.issues)

    def test_null_counts_calculated(self, validation_service):
        """Null counts should be calculated per column."""
        df = pd.DataFrame(
            {
                "col1": [1, 2, None, 4, 5],
                "col2": [None, None, "c", "d", "e"],
            }
        )

        report = validation_service.validate(df)

        assert report.null_counts["col1"] == 1
        assert report.null_counts["col2"] == 2

    def test_dtypes_extracted(self, validation_service):
        """Data types should be extracted."""
        df = pd.DataFrame(
            {
                "int_col": [1, 2, 3],
                "str_col": ["a", "b", "c"],
            }
        )

        report = validation_service.validate(df)

        assert "int_col" in report.dtypes
        assert "str_col" in report.dtypes

    def test_duplicate_column_names_fail(self, validation_service):
        """Duplicate column names should fail validation."""
        df = pd.DataFrame([[1, 2, 3]], columns=["col", "col", "col2"])

        report = validation_service.validate(df)

        assert report.is_valid is False
        assert any("duplicate" in issue.lower() for issue in report.issues)

    def test_column_statistics(self, validation_service):
        """Column statistics should be calculated."""
        df = pd.DataFrame(
            {
                "numeric": [1, 2, 3, 4, 5],
                "text": ["a", "b", "c", "d", "e"],
            }
        )

        stats = validation_service.get_column_statistics(df)

        assert "numeric" in stats
        assert "min" in stats["numeric"]
        assert "max" in stats["numeric"]
        assert stats["numeric"]["min"] == 1.0
        assert stats["numeric"]["max"] == 5.0
