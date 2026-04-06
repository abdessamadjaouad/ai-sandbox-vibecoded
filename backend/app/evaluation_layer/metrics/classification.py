# backend/app/evaluation_layer/metrics/classification.py
"""
Classification metrics computation.

Computes standard classification metrics for binary and multi-class problems.
"""

from typing import Any

import numpy as np
from pydantic import BaseModel, Field
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report,
    log_loss,
    matthews_corrcoef,
    balanced_accuracy_score,
    cohen_kappa_score,
)

import structlog

logger = structlog.get_logger(__name__)


class ClassificationMetricsResult(BaseModel):
    """Result of classification metrics computation."""

    accuracy: float = Field(..., description="Accuracy score")
    balanced_accuracy: float = Field(..., description="Balanced accuracy (handles imbalanced classes)")
    precision: float = Field(..., description="Precision score (weighted for multi-class)")
    recall: float = Field(..., description="Recall score (weighted for multi-class)")
    f1: float = Field(..., description="F1 score (weighted for multi-class)")
    auc_roc: float | None = Field(None, description="AUC-ROC score (requires probabilities)")
    log_loss_value: float | None = Field(None, description="Log loss (requires probabilities)")
    mcc: float = Field(..., description="Matthews Correlation Coefficient")
    cohen_kappa: float = Field(..., description="Cohen's Kappa score")
    confusion_matrix: list[list[int]] = Field(..., description="Confusion matrix")
    class_labels: list[str] = Field(default_factory=list, description="Class labels")
    per_class_metrics: dict[str, dict[str, float]] | None = Field(None, description="Per-class precision, recall, f1")
    is_binary: bool = Field(..., description="Whether this is binary classification")
    support: int = Field(..., description="Total number of samples")


class ClassificationMetrics:
    """
    Compute comprehensive classification metrics.

    Supports both binary and multi-class classification with automatic
    detection and appropriate metric computation.
    """

    def __init__(self, class_labels: list[str] | None = None):
        """
        Initialize classification metrics calculator.

        Args:
            class_labels: Optional list of class labels for reporting
        """
        self.class_labels = class_labels

    def compute(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        y_prob: np.ndarray | None = None,
    ) -> ClassificationMetricsResult:
        """
        Compute all classification metrics.

        Args:
            y_true: Ground truth labels
            y_pred: Predicted labels
            y_prob: Predicted probabilities (optional, for AUC and log_loss)

        Returns:
            ClassificationMetricsResult with all computed metrics

        Raises:
            ValueError: If inputs have mismatched lengths
        """
        if len(y_true) != len(y_pred):
            raise ValueError(f"y_true and y_pred must have same length: {len(y_true)} vs {len(y_pred)}")

        # Determine if binary or multi-class
        unique_classes = np.unique(np.concatenate([y_true, y_pred]))
        is_binary = len(unique_classes) == 2
        average = "binary" if is_binary else "weighted"

        # Set class labels
        class_labels = self.class_labels or [str(c) for c in unique_classes]

        # Basic metrics
        accuracy = float(accuracy_score(y_true, y_pred))
        balanced_acc = float(balanced_accuracy_score(y_true, y_pred))
        precision = float(precision_score(y_true, y_pred, average=average, zero_division=0))
        recall = float(recall_score(y_true, y_pred, average=average, zero_division=0))
        f1 = float(f1_score(y_true, y_pred, average=average, zero_division=0))
        mcc = float(matthews_corrcoef(y_true, y_pred))
        kappa = float(cohen_kappa_score(y_true, y_pred))

        # Confusion matrix
        cm = confusion_matrix(y_true, y_pred, labels=unique_classes).tolist()

        # AUC-ROC and log loss (require probabilities)
        auc_roc = None
        log_loss_value = None
        if y_prob is not None:
            try:
                if is_binary:
                    # For binary, use probability of positive class
                    prob_positive = y_prob[:, 1] if y_prob.ndim == 2 else y_prob
                    auc_roc = float(roc_auc_score(y_true, prob_positive))
                else:
                    auc_roc = float(roc_auc_score(y_true, y_prob, multi_class="ovr", average="weighted"))
                log_loss_value = float(log_loss(y_true, y_prob))
            except Exception as e:
                logger.warning("auc_computation_failed", error=str(e))

        # Per-class metrics
        per_class = self._compute_per_class_metrics(y_true, y_pred, class_labels)

        logger.info(
            "classification_metrics_computed",
            accuracy=accuracy,
            f1=f1,
            is_binary=is_binary,
            num_classes=len(unique_classes),
        )

        return ClassificationMetricsResult(
            accuracy=accuracy,
            balanced_accuracy=balanced_acc,
            precision=precision,
            recall=recall,
            f1=f1,
            auc_roc=auc_roc,
            log_loss_value=log_loss_value,
            mcc=mcc,
            cohen_kappa=kappa,
            confusion_matrix=cm,
            class_labels=class_labels,
            per_class_metrics=per_class,
            is_binary=is_binary,
            support=len(y_true),
        )

    def _compute_per_class_metrics(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        class_labels: list[str],
    ) -> dict[str, dict[str, float]]:
        """
        Compute per-class precision, recall, and f1.

        Args:
            y_true: Ground truth labels
            y_pred: Predicted labels
            class_labels: Class label names

        Returns:
            Dict mapping class label to metrics dict
        """
        report = classification_report(y_true, y_pred, output_dict=True, zero_division=0)

        per_class = {}
        unique_classes = np.unique(np.concatenate([y_true, y_pred]))

        for i, cls in enumerate(unique_classes):
            label = class_labels[i] if i < len(class_labels) else str(cls)
            cls_key = str(cls)
            if cls_key in report:
                per_class[label] = {
                    "precision": float(report[cls_key]["precision"]),
                    "recall": float(report[cls_key]["recall"]),
                    "f1": float(report[cls_key]["f1-score"]),
                    "support": int(report[cls_key]["support"]),
                }

        return per_class

    def compute_from_dict(
        self,
        y_true: list[Any],
        y_pred: list[Any],
        y_prob: list[list[float]] | None = None,
    ) -> ClassificationMetricsResult:
        """
        Compute metrics from Python lists (convenience method).

        Args:
            y_true: Ground truth labels as list
            y_pred: Predicted labels as list
            y_prob: Predicted probabilities as nested list

        Returns:
            ClassificationMetricsResult
        """
        y_true_arr = np.array(y_true)
        y_pred_arr = np.array(y_pred)
        y_prob_arr = np.array(y_prob) if y_prob is not None else None

        return self.compute(y_true_arr, y_pred_arr, y_prob_arr)
