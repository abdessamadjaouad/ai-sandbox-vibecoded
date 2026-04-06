# tests/unit/test_evaluation_layer/test_metrics.py
"""Tests for evaluation metrics module."""

import numpy as np
import pytest

from backend.app.evaluation_layer.metrics import (
    ClassificationMetrics,
    RegressionMetrics,
    MetricsCalculator,
)
from backend.app.models.experiment import TaskType


class TestClassificationMetrics:
    """Tests for classification metrics computation."""

    def test_compute_binary_classification_metrics(self):
        """Computes expected binary classification metrics."""
        calculator = ClassificationMetrics()

        y_true = np.array([0, 1, 1, 0, 1, 0])
        y_pred = np.array([0, 1, 0, 0, 1, 1])

        result = calculator.compute(y_true=y_true, y_pred=y_pred)

        assert result.is_binary is True
        assert result.support == 6
        assert result.accuracy == pytest.approx(4 / 6)
        assert result.precision == pytest.approx(2 / 3)
        assert result.recall == pytest.approx(2 / 3)
        assert result.f1 == pytest.approx(2 / 3)
        assert len(result.confusion_matrix) == 2

    def test_compute_with_probabilities_includes_auc(self):
        """Computes AUC and log-loss when probabilities are provided."""
        calculator = ClassificationMetrics()

        y_true = np.array([0, 1, 1, 0])
        y_pred = np.array([0, 1, 1, 0])
        y_prob = np.array(
            [
                [0.9, 0.1],
                [0.1, 0.9],
                [0.2, 0.8],
                [0.8, 0.2],
            ]
        )

        result = calculator.compute(y_true=y_true, y_pred=y_pred, y_prob=y_prob)

        assert result.auc_roc is not None
        assert result.log_loss_value is not None
        assert result.auc_roc == pytest.approx(1.0)

    def test_compute_raises_on_mismatched_lengths(self):
        """Raises ValueError when y_true/y_pred lengths differ."""
        calculator = ClassificationMetrics()

        with pytest.raises(ValueError):
            calculator.compute(y_true=np.array([0, 1]), y_pred=np.array([0]))


class TestRegressionMetrics:
    """Tests for regression metrics computation."""

    def test_compute_regression_metrics(self):
        """Computes expected regression metrics."""
        calculator = RegressionMetrics()

        y_true = np.array([1.0, 2.0, 3.0, 4.0])
        y_pred = np.array([1.1, 1.9, 3.2, 3.8])

        result = calculator.compute(y_true=y_true, y_pred=y_pred)

        assert result.support == 4
        assert result.mse >= 0
        assert result.rmse >= 0
        assert result.mae >= 0
        assert -1 <= result.r2 <= 1
        assert result.y_true_mean == pytest.approx(2.5)

    def test_compute_handles_zero_targets_for_mape(self):
        """Keeps MAPE as None when y_true contains zeros."""
        calculator = RegressionMetrics()

        y_true = np.array([0.0, 1.0, 2.0])
        y_pred = np.array([0.1, 1.1, 1.9])

        result = calculator.compute(y_true=y_true, y_pred=y_pred)

        assert result.mape is None


class TestMetricsCalculator:
    """Tests for unified metrics calculator."""

    def test_dispatches_classification(self):
        """Dispatches to classification metrics for classification task."""
        calculator = MetricsCalculator()

        result = calculator.compute(
            task_type=TaskType.CLASSIFICATION,
            y_true=[0, 1, 1, 0],
            y_pred=[0, 1, 0, 0],
        )

        assert hasattr(result, "accuracy")
        assert hasattr(result, "f1")

    def test_dispatches_regression(self):
        """Dispatches to regression metrics for regression task."""
        calculator = MetricsCalculator()

        result = calculator.compute(
            task_type=TaskType.REGRESSION,
            y_true=[1.0, 2.0, 3.0],
            y_pred=[1.1, 1.9, 2.8],
        )

        assert hasattr(result, "rmse")
        assert hasattr(result, "r2")

    def test_extract_metrics_for_scoring_filters_complex_fields(self):
        """Extracts only scalar numeric metrics for scoring."""
        calculator = MetricsCalculator()

        result = calculator.compute(
            task_type=TaskType.CLASSIFICATION,
            y_true=[0, 1, 1, 0],
            y_pred=[0, 1, 0, 0],
        )
        extracted = calculator.extract_metrics_for_scoring(result, TaskType.CLASSIFICATION)

        assert "accuracy" in extracted
        assert "f1" in extracted
        assert "confusion_matrix" not in extracted
        assert "support" not in extracted
