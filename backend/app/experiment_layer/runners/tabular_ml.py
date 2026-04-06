# backend/app/experiment_layer/runners/tabular_ml.py
"""
Tabular ML runner — trains and evaluates tabular ML models.

Handles scikit-learn compatible models (sklearn, XGBoost, LightGBM, CatBoost).
Computes classification and regression metrics.
"""

import time
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    mean_squared_error,
    mean_absolute_error,
    r2_score,
    confusion_matrix,
)
from sklearn.preprocessing import LabelEncoder

from backend.app.models.experiment import TaskType, ModelFamily
from backend.app.experiment_layer.orchestrator.catalogue import get_catalogue
from backend.app.experiment_layer.orchestrator.state import ModelResult

import structlog

logger = structlog.get_logger(__name__)


class TabularMLRunner:
    """
    Runner for tabular ML experiments.

    Trains scikit-learn compatible models and computes standard metrics
    for classification and regression tasks.
    """

    def __init__(self, random_seed: int = 42):
        """
        Initialize the runner.

        Args:
            random_seed: Random seed for reproducibility
        """
        self.random_seed = random_seed
        self.catalogue = get_catalogue()
        self._label_encoder: LabelEncoder | None = None

    def train_and_evaluate(
        self,
        model_config: dict[str, Any],
        task_type: TaskType,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: pd.DataFrame | None = None,
        y_val: pd.Series | None = None,
        X_test: pd.DataFrame | None = None,
        y_test: pd.Series | None = None,
    ) -> ModelResult:
        """
        Train a model and evaluate on validation/test sets.

        Args:
            model_config: Configuration dict with name, family, hyperparameters
            task_type: Classification or regression
            X_train: Training features
            y_train: Training target
            X_val: Validation features (optional)
            y_val: Validation target (optional)
            X_test: Test features (optional)
            y_test: Test target (optional)

        Returns:
            ModelResult with metrics and metadata
        """
        model_name = model_config.get("name", "Unknown Model")
        model_family = model_config.get("family", ModelFamily.SKLEARN.value)
        hyperparameters = model_config.get("hyperparameters", {})

        logger.info(
            "training_model",
            model_name=model_name,
            task_type=task_type.value,
            train_samples=len(X_train),
        )

        try:
            # Instantiate model
            model = self.catalogue.instantiate_model(
                model_name,
                hyperparameters=hyperparameters,
                random_seed=self.random_seed,
            )

            # Encode labels for classification if needed
            y_train_encoded = self._encode_labels(y_train, task_type, fit=True)
            y_val_encoded = self._encode_labels(y_val, task_type) if y_val is not None else None
            y_test_encoded = self._encode_labels(y_test, task_type) if y_test is not None else None

            # Train model
            start_time = time.perf_counter()
            model.fit(X_train, y_train_encoded)
            training_duration = time.perf_counter() - start_time

            # Compute metrics on validation set (or test if no val)
            eval_X = X_val if X_val is not None else X_test
            eval_y = y_val_encoded if y_val_encoded is not None else y_test_encoded

            metrics = {}
            inference_latency_ms = None

            if eval_X is not None and eval_y is not None:
                # Measure inference latency
                latency_start = time.perf_counter()
                y_pred = model.predict(eval_X)
                inference_latency_ms = (time.perf_counter() - latency_start) * 1000 / len(eval_X)

                # Compute metrics based on task type
                if task_type == TaskType.CLASSIFICATION:
                    metrics = self._compute_classification_metrics(eval_y, y_pred, model, eval_X)
                elif task_type == TaskType.REGRESSION:
                    metrics = self._compute_regression_metrics(eval_y, y_pred)

            # If we have a separate test set, compute test metrics too
            if X_test is not None and y_test_encoded is not None and X_val is not None:
                y_test_pred = model.predict(X_test)
                if task_type == TaskType.CLASSIFICATION:
                    test_metrics = self._compute_classification_metrics(y_test_encoded, y_test_pred, model, X_test)
                else:
                    test_metrics = self._compute_regression_metrics(y_test_encoded, y_test_pred)
                # Prefix test metrics
                for key, value in test_metrics.items():
                    metrics[f"test_{key}"] = value

            logger.info(
                "model_trained",
                model_name=model_name,
                training_duration_seconds=training_duration,
                metrics=metrics,
            )

            return ModelResult(
                model_name=model_name,
                model_family=model_family,
                model_config=model_config,
                hyperparameters=hyperparameters,
                metrics=metrics,
                global_score=None,  # Computed later in scoring node
                rank=None,
                training_duration_seconds=training_duration,
                inference_latency_ms=inference_latency_ms,
                artefact_path=None,  # Set after saving
                mlflow_run_id=None,  # Set by tracking
                error_message=None,
                predictions=y_pred.tolist() if eval_X is not None else None,
            )

        except Exception as e:
            logger.error(
                "model_training_failed",
                model_name=model_name,
                error=str(e),
            )
            return ModelResult(
                model_name=model_name,
                model_family=model_family,
                model_config=model_config,
                hyperparameters=hyperparameters,
                metrics={},
                global_score=None,
                rank=None,
                training_duration_seconds=None,
                inference_latency_ms=None,
                artefact_path=None,
                mlflow_run_id=None,
                error_message=str(e),
                predictions=None,
            )

    def _encode_labels(
        self,
        y: pd.Series | None,
        task_type: TaskType,
        fit: bool = False,
    ) -> np.ndarray | None:
        """
        Encode labels for classification if needed.

        Args:
            y: Target series
            task_type: Task type
            fit: Whether to fit the encoder (only on training data)

        Returns:
            Encoded array or original values for regression
        """
        if y is None:
            return None

        if task_type != TaskType.CLASSIFICATION:
            return y.values

        # Check if labels need encoding (non-numeric)
        if not np.issubdtype(y.dtype, np.number):
            if fit:
                self._label_encoder = LabelEncoder()
                return self._label_encoder.fit_transform(y)
            elif self._label_encoder is not None:
                return self._label_encoder.transform(y)

        return y.values

    def _compute_classification_metrics(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        model: Any,
        X: pd.DataFrame,
    ) -> dict[str, float]:
        """
        Compute classification metrics.

        Args:
            y_true: True labels
            y_pred: Predicted labels
            model: Trained model (for probability predictions)
            X: Features (for probability predictions)

        Returns:
            Dictionary of metric name to value
        """
        metrics = {
            "accuracy": float(accuracy_score(y_true, y_pred)),
        }

        # Handle multi-class vs binary classification
        unique_classes = np.unique(y_true)
        is_binary = len(unique_classes) == 2
        average = "binary" if is_binary else "weighted"

        # Precision, Recall, F1
        metrics["precision"] = float(precision_score(y_true, y_pred, average=average, zero_division=0))
        metrics["recall"] = float(recall_score(y_true, y_pred, average=average, zero_division=0))
        metrics["f1"] = float(f1_score(y_true, y_pred, average=average, zero_division=0))

        # AUC-ROC (if model supports predict_proba)
        if hasattr(model, "predict_proba"):
            try:
                y_prob = model.predict_proba(X)
                if is_binary:
                    metrics["auc_roc"] = float(roc_auc_score(y_true, y_prob[:, 1]))
                else:
                    metrics["auc_roc"] = float(roc_auc_score(y_true, y_prob, multi_class="ovr", average="weighted"))
            except Exception:
                # AUC may fail for some edge cases
                pass

        # Confusion matrix (flattened for JSON storage)
        cm = confusion_matrix(y_true, y_pred)
        metrics["confusion_matrix"] = cm.tolist()

        return metrics

    def _compute_regression_metrics(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
    ) -> dict[str, float]:
        """
        Compute regression metrics.

        Args:
            y_true: True values
            y_pred: Predicted values

        Returns:
            Dictionary of metric name to value
        """
        return {
            "mse": float(mean_squared_error(y_true, y_pred)),
            "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
            "mae": float(mean_absolute_error(y_true, y_pred)),
            "r2": float(r2_score(y_true, y_pred)),
        }

    def run_multiple_models(
        self,
        models_config: list[dict[str, Any]],
        task_type: TaskType,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: pd.DataFrame | None = None,
        y_val: pd.Series | None = None,
        X_test: pd.DataFrame | None = None,
        y_test: pd.Series | None = None,
    ) -> list[ModelResult]:
        """
        Train and evaluate multiple models.

        Args:
            models_config: List of model configurations
            task_type: Classification or regression
            X_train: Training features
            y_train: Training target
            X_val: Validation features (optional)
            y_val: Validation target (optional)
            X_test: Test features (optional)
            y_test: Test target (optional)

        Returns:
            List of ModelResult objects
        """
        results = []
        for config in models_config:
            if not config.get("enabled", True):
                continue
            result = self.train_and_evaluate(
                model_config=config,
                task_type=task_type,
                X_train=X_train,
                y_train=y_train,
                X_val=X_val,
                y_val=y_val,
                X_test=X_test,
                y_test=y_test,
            )
            results.append(result)
        return results
