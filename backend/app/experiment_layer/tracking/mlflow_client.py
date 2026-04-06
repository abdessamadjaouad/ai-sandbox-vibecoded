# backend/app/experiment_layer/tracking/mlflow_client.py
"""
MLflow tracking wrapper for experiment logging.

Provides a clean interface for logging experiments, runs, metrics,
parameters, and artefacts to MLflow.
"""

import os
from typing import Any
from contextlib import contextmanager

import mlflow
from mlflow.tracking import MlflowClient

from backend.app.core.config import settings
from backend.app.experiment_layer.orchestrator.state import ModelResult

import structlog

logger = structlog.get_logger(__name__)


class MLflowTracker:
    """
    Wrapper for MLflow tracking operations.

    Provides methods for creating experiments, logging runs,
    and tracking metrics/artefacts in a structured way.
    """

    def __init__(self, tracking_uri: str | None = None):
        """
        Initialize the MLflow tracker.

        Args:
            tracking_uri: MLflow tracking URI (defaults to config)
        """
        self.tracking_uri = tracking_uri or settings.mlflow_tracking_uri
        mlflow.set_tracking_uri(self.tracking_uri)
        self._client = MlflowClient(tracking_uri=self.tracking_uri)

    def get_or_create_experiment(self, name: str) -> str:
        """
        Get or create an MLflow experiment by name.

        Args:
            name: Experiment name

        Returns:
            Experiment ID
        """
        experiment = mlflow.get_experiment_by_name(name)
        if experiment is None:
            experiment_id = mlflow.create_experiment(name)
            logger.info("mlflow_experiment_created", name=name, experiment_id=experiment_id)
        else:
            experiment_id = experiment.experiment_id
            logger.debug("mlflow_experiment_exists", name=name, experiment_id=experiment_id)
        return experiment_id

    @contextmanager
    def start_run(
        self,
        experiment_id: str,
        run_name: str,
        tags: dict[str, str] | None = None,
        nested: bool = False,
    ):
        """
        Context manager for starting an MLflow run.

        Args:
            experiment_id: MLflow experiment ID
            run_name: Name for this run
            tags: Optional tags to attach
            nested: Whether this is a nested run

        Yields:
            Active MLflow run
        """
        with mlflow.start_run(
            experiment_id=experiment_id,
            run_name=run_name,
            tags=tags,
            nested=nested,
        ) as run:
            logger.info(
                "mlflow_run_started",
                run_id=run.info.run_id,
                run_name=run_name,
            )
            yield run

    def log_params(self, params: dict[str, Any]) -> None:
        """
        Log parameters to the active run.

        Args:
            params: Dictionary of parameter names to values
        """
        # MLflow has a limit on param value length (500 chars)
        for key, value in params.items():
            str_value = str(value)
            if len(str_value) > 500:
                str_value = str_value[:497] + "..."
            try:
                mlflow.log_param(key, str_value)
            except Exception as e:
                logger.warning("mlflow_param_log_failed", key=key, error=str(e))

    def log_metrics(self, metrics: dict[str, float], step: int | None = None) -> None:
        """
        Log metrics to the active run.

        Args:
            metrics: Dictionary of metric names to values
            step: Optional step number for time-series metrics
        """
        for key, value in metrics.items():
            # Skip non-numeric values (like confusion matrix)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                try:
                    mlflow.log_metric(key, value, step=step)
                except Exception as e:
                    logger.warning("mlflow_metric_log_failed", key=key, error=str(e))

    def log_model_result(
        self,
        result: ModelResult,
        experiment_id: str,
        parent_run_id: str | None = None,
    ) -> str | None:
        """
        Log a complete model result as a nested run.

        Args:
            result: ModelResult from the runner
            experiment_id: MLflow experiment ID
            parent_run_id: Parent run ID for nested runs

        Returns:
            Run ID for this model's run
        """
        model_name = result.get("model_name", "unknown")

        tags = {
            "model_name": model_name,
            "model_family": result.get("model_family", "unknown"),
        }
        if parent_run_id:
            tags["mlflow.parentRunId"] = parent_run_id

        try:
            with self.start_run(
                experiment_id=experiment_id,
                run_name=model_name,
                tags=tags,
                nested=parent_run_id is not None,
            ) as run:
                # Log hyperparameters
                hyperparams = result.get("hyperparameters") or {}
                self.log_params(hyperparams)

                # Log training metadata
                if result.get("training_duration_seconds"):
                    mlflow.log_metric("training_duration_seconds", result["training_duration_seconds"])
                if result.get("inference_latency_ms"):
                    mlflow.log_metric("inference_latency_ms", result["inference_latency_ms"])
                if result.get("global_score") is not None:
                    mlflow.log_metric("global_score", result["global_score"])

                # Log metrics
                metrics = result.get("metrics") or {}
                self.log_metrics(metrics)

                # Log error if any
                if result.get("error_message"):
                    mlflow.set_tag("error", "true")
                    mlflow.set_tag("error_message", result["error_message"][:500])

                return run.info.run_id

        except Exception as e:
            logger.error(
                "mlflow_model_result_log_failed",
                model_name=model_name,
                error=str(e),
            )
            return None

    def log_experiment_summary(
        self,
        experiment_id: str,
        run_name: str,
        total_models: int,
        successful_models: int,
        best_model_name: str | None,
        best_model_score: float | None,
        recommendation: str | None,
        duration_seconds: float | None,
    ) -> str | None:
        """
        Log the overall experiment summary as the parent run.

        Args:
            experiment_id: MLflow experiment ID
            run_name: Name for the parent run
            total_models: Total number of models evaluated
            successful_models: Number of successful model runs
            best_model_name: Name of the best performing model
            best_model_score: Score of the best model
            recommendation: Plain-language recommendation
            duration_seconds: Total experiment duration

        Returns:
            Parent run ID
        """
        try:
            with self.start_run(
                experiment_id=experiment_id,
                run_name=run_name,
                tags={"run_type": "experiment_summary"},
            ) as run:
                mlflow.log_param("total_models", total_models)
                mlflow.log_param("successful_models", successful_models)

                if best_model_name:
                    mlflow.log_param("best_model", best_model_name)
                if best_model_score is not None:
                    mlflow.log_metric("best_score", best_model_score)
                if duration_seconds:
                    mlflow.log_metric("total_duration_seconds", duration_seconds)
                if recommendation:
                    mlflow.set_tag("recommendation", recommendation[:500])

                return run.info.run_id

        except Exception as e:
            logger.error("mlflow_summary_log_failed", error=str(e))
            return None

    def health_check(self) -> bool:
        """
        Check if MLflow tracking server is reachable.

        Returns:
            True if healthy, False otherwise
        """
        try:
            # List experiments as a health check
            self._client.search_experiments(max_results=1)
            return True
        except Exception as e:
            logger.warning("mlflow_health_check_failed", error=str(e))
            return False


# Global tracker instance
_tracker: MLflowTracker | None = None


def get_tracker() -> MLflowTracker:
    """
    Get the global MLflow tracker instance.

    Returns:
        MLflowTracker singleton instance
    """
    global _tracker
    if _tracker is None:
        _tracker = MLflowTracker()
    return _tracker
