# backend/app/evaluation_layer/metrics/regression.py
"""
Regression metrics computation.

Computes standard regression metrics for continuous target prediction.
"""

import numpy as np
from pydantic import BaseModel, Field
from sklearn.metrics import (
    mean_squared_error,
    mean_absolute_error,
    r2_score,
    median_absolute_error,
    max_error,
    mean_absolute_percentage_error,
    explained_variance_score,
)

import structlog

logger = structlog.get_logger(__name__)


class RegressionMetricsResult(BaseModel):
    """Result of regression metrics computation."""

    mse: float = Field(..., description="Mean Squared Error")
    rmse: float = Field(..., description="Root Mean Squared Error")
    mae: float = Field(..., description="Mean Absolute Error")
    mape: float | None = Field(None, description="Mean Absolute Percentage Error (if y_true has no zeros)")
    median_ae: float = Field(..., description="Median Absolute Error")
    max_error_value: float = Field(..., description="Maximum Error")
    r2: float = Field(..., description="R-squared (coefficient of determination)")
    explained_variance: float = Field(..., description="Explained variance score")
    residual_std: float = Field(..., description="Standard deviation of residuals")
    support: int = Field(..., description="Total number of samples")
    y_true_mean: float = Field(..., description="Mean of true values")
    y_true_std: float = Field(..., description="Std dev of true values")
    y_pred_mean: float = Field(..., description="Mean of predicted values")
    y_pred_std: float = Field(..., description="Std dev of predicted values")


class RegressionMetrics:
    """
    Compute comprehensive regression metrics.

    Provides a full suite of regression metrics for model evaluation.
    """

    def compute(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
    ) -> RegressionMetricsResult:
        """
        Compute all regression metrics.

        Args:
            y_true: Ground truth values
            y_pred: Predicted values

        Returns:
            RegressionMetricsResult with all computed metrics

        Raises:
            ValueError: If inputs have mismatched lengths
        """
        if len(y_true) != len(y_pred):
            raise ValueError(f"y_true and y_pred must have same length: {len(y_true)} vs {len(y_pred)}")

        y_true = np.asarray(y_true)
        y_pred = np.asarray(y_pred)

        # Core metrics
        mse = float(mean_squared_error(y_true, y_pred))
        rmse = float(np.sqrt(mse))
        mae = float(mean_absolute_error(y_true, y_pred))
        median_ae = float(median_absolute_error(y_true, y_pred))
        max_err = float(max_error(y_true, y_pred))
        r2 = float(r2_score(y_true, y_pred))
        explained_var = float(explained_variance_score(y_true, y_pred))

        # MAPE - only if no zeros in y_true to avoid division by zero
        mape = None
        if not np.any(y_true == 0):
            try:
                mape = float(mean_absolute_percentage_error(y_true, y_pred))
            except Exception:
                pass

        # Residual statistics
        residuals = y_true - y_pred
        residual_std = float(np.std(residuals))

        # Distribution statistics
        y_true_mean = float(np.mean(y_true))
        y_true_std = float(np.std(y_true))
        y_pred_mean = float(np.mean(y_pred))
        y_pred_std = float(np.std(y_pred))

        logger.info(
            "regression_metrics_computed",
            rmse=rmse,
            r2=r2,
            mae=mae,
            support=len(y_true),
        )

        return RegressionMetricsResult(
            mse=mse,
            rmse=rmse,
            mae=mae,
            mape=mape,
            median_ae=median_ae,
            max_error_value=max_err,
            r2=r2,
            explained_variance=explained_var,
            residual_std=residual_std,
            support=len(y_true),
            y_true_mean=y_true_mean,
            y_true_std=y_true_std,
            y_pred_mean=y_pred_mean,
            y_pred_std=y_pred_std,
        )

    def compute_from_dict(
        self,
        y_true: list[float],
        y_pred: list[float],
    ) -> RegressionMetricsResult:
        """
        Compute metrics from Python lists (convenience method).

        Args:
            y_true: Ground truth values as list
            y_pred: Predicted values as list

        Returns:
            RegressionMetricsResult
        """
        return self.compute(np.array(y_true), np.array(y_pred))

    def compute_custom_metrics(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        custom_thresholds: dict[str, float] | None = None,
    ) -> dict[str, float]:
        """
        Compute custom threshold-based metrics.

        Args:
            y_true: Ground truth values
            y_pred: Predicted values
            custom_thresholds: Dict of threshold names to values

        Returns:
            Dict of custom metric results
        """
        if custom_thresholds is None:
            custom_thresholds = {"within_10_pct": 0.10, "within_5_pct": 0.05}

        custom_metrics = {}
        residuals = np.abs(y_true - y_pred)

        for name, threshold in custom_thresholds.items():
            # Percentage of predictions within threshold of true value
            if "pct" in name:
                within_threshold = np.abs(y_pred - y_true) / np.maximum(np.abs(y_true), 1e-8) < threshold
            else:
                within_threshold = residuals < threshold
            custom_metrics[name] = float(np.mean(within_threshold))

        return custom_metrics
