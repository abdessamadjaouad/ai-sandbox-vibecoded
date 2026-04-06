# backend/app/evaluation_layer/metrics/calculator.py
"""
Unified metrics calculator that dispatches to appropriate metric type.

Provides a single entry point for metrics computation across all task types.
"""

from typing import Any

import numpy as np

from backend.app.models.experiment import TaskType
from backend.app.evaluation_layer.metrics.classification import (
    ClassificationMetrics,
    ClassificationMetricsResult,
)
from backend.app.evaluation_layer.metrics.regression import (
    RegressionMetrics,
    RegressionMetricsResult,
)

import structlog

logger = structlog.get_logger(__name__)


class MetricsCalculator:
    """
    Unified metrics calculator that handles all task types.

    Automatically selects the appropriate metrics based on task type
    and provides a consistent interface for evaluation.
    """

    def __init__(self, class_labels: list[str] | None = None):
        """
        Initialize the metrics calculator.

        Args:
            class_labels: Optional class labels for classification tasks
        """
        self._classification = ClassificationMetrics(class_labels=class_labels)
        self._regression = RegressionMetrics()

    def compute(
        self,
        task_type: TaskType,
        y_true: np.ndarray | list,
        y_pred: np.ndarray | list,
        y_prob: np.ndarray | list | None = None,
    ) -> ClassificationMetricsResult | RegressionMetricsResult:
        """
        Compute metrics based on task type.

        Args:
            task_type: Classification or regression
            y_true: Ground truth values/labels
            y_pred: Predicted values/labels
            y_prob: Predicted probabilities (classification only)

        Returns:
            ClassificationMetricsResult or RegressionMetricsResult

        Raises:
            ValueError: If task type is not supported
        """
        # Convert lists to numpy arrays
        y_true = np.asarray(y_true)
        y_pred = np.asarray(y_pred)
        if y_prob is not None:
            y_prob = np.asarray(y_prob)

        if task_type == TaskType.CLASSIFICATION:
            return self._classification.compute(y_true, y_pred, y_prob)
        elif task_type == TaskType.REGRESSION:
            return self._regression.compute(y_true, y_pred)
        else:
            raise ValueError(f"Unsupported task type: {task_type}")

    def compute_from_results(
        self,
        task_type: TaskType,
        results: list[dict[str, Any]],
        ground_truth: list[Any],
    ) -> list[dict[str, Any]]:
        """
        Compute metrics for multiple model results.

        Enriches each result dict with computed metrics.

        Args:
            task_type: Classification or regression
            results: List of result dicts with 'predictions' key
            ground_truth: Ground truth values

        Returns:
            List of results with added metrics
        """
        enriched = []

        for result in results:
            predictions = result.get("predictions")
            probabilities = result.get("probabilities")

            if predictions is None:
                # Skip results without predictions
                enriched.append(result)
                continue

            try:
                metrics_result = self.compute(
                    task_type=task_type,
                    y_true=ground_truth,
                    y_pred=predictions,
                    y_prob=probabilities,
                )

                # Convert metrics result to dict and merge
                metrics_dict = metrics_result.model_dump()
                result_copy = dict(result)
                result_copy["computed_metrics"] = metrics_dict
                enriched.append(result_copy)

            except Exception as e:
                logger.error(
                    "metrics_computation_failed",
                    model_name=result.get("model_name"),
                    error=str(e),
                )
                enriched.append(result)

        return enriched

    def get_primary_metric(self, task_type: TaskType) -> str:
        """
        Get the primary metric name for a task type.

        Args:
            task_type: Classification or regression

        Returns:
            Primary metric name
        """
        if task_type == TaskType.CLASSIFICATION:
            return "f1"
        elif task_type == TaskType.REGRESSION:
            return "rmse"
        else:
            return "accuracy"

    def get_all_metric_names(self, task_type: TaskType) -> list[str]:
        """
        Get all metric names for a task type.

        Args:
            task_type: Classification or regression

        Returns:
            List of metric names
        """
        if task_type == TaskType.CLASSIFICATION:
            return [
                "accuracy",
                "balanced_accuracy",
                "precision",
                "recall",
                "f1",
                "auc_roc",
                "log_loss_value",
                "mcc",
                "cohen_kappa",
            ]
        elif task_type == TaskType.REGRESSION:
            return [
                "mse",
                "rmse",
                "mae",
                "mape",
                "median_ae",
                "max_error_value",
                "r2",
                "explained_variance",
            ]
        else:
            return []

    def extract_metrics_for_scoring(
        self,
        metrics_result: ClassificationMetricsResult | RegressionMetricsResult,
        task_type: TaskType,
    ) -> dict[str, float]:
        """
        Extract metrics suitable for scoring.

        Filters out non-numeric and complex metrics like confusion matrix.

        Args:
            metrics_result: The computed metrics result
            task_type: Task type for context

        Returns:
            Dict of metric name to float value
        """
        metrics_dict = metrics_result.model_dump()

        # Exclude non-scorable fields
        excluded = {
            "confusion_matrix",
            "class_labels",
            "per_class_metrics",
            "is_binary",
            "support",
            "y_true_mean",
            "y_true_std",
            "y_pred_mean",
            "y_pred_std",
        }

        scorable = {}
        for key, value in metrics_dict.items():
            if key in excluded:
                continue
            if value is None:
                continue
            if isinstance(value, (int, float)):
                scorable[key] = float(value)

        return scorable
