# tests/unit/test_experiment_layer/test_mlflow_tracker.py
"""Tests for MLflow tracking integration."""

from unittest.mock import MagicMock, patch

import pytest

from backend.app.experiment_layer.tracking.mlflow_client import MLflowTracker, get_tracker


class TestMLflowTracker:
    """Tests for MLflowTracker class."""

    @pytest.fixture
    def mock_mlflow(self):
        """Mock mlflow module."""
        with patch("backend.app.experiment_layer.tracking.mlflow_client.mlflow") as mock:
            mock.get_experiment_by_name.return_value = None
            mock.create_experiment.return_value = "exp-123"
            yield mock

    @pytest.fixture
    def mock_client(self):
        """Mock MlflowClient."""
        with patch("backend.app.experiment_layer.tracking.mlflow_client.MlflowClient") as mock:
            yield mock

    def test_get_or_create_experiment_creates_new(self, mock_mlflow, mock_client):
        """get_or_create_experiment creates experiment when not exists."""
        mock_mlflow.get_experiment_by_name.return_value = None
        mock_mlflow.create_experiment.return_value = "new-exp-id"

        tracker = MLflowTracker(tracking_uri="http://test:5000")
        exp_id = tracker.get_or_create_experiment("Test Experiment")

        assert exp_id == "new-exp-id"
        mock_mlflow.create_experiment.assert_called_once_with("Test Experiment")

    def test_get_or_create_experiment_returns_existing(self, mock_mlflow, mock_client):
        """get_or_create_experiment returns existing experiment ID."""
        mock_experiment = MagicMock()
        mock_experiment.experiment_id = "existing-exp-id"
        mock_mlflow.get_experiment_by_name.return_value = mock_experiment

        tracker = MLflowTracker(tracking_uri="http://test:5000")
        exp_id = tracker.get_or_create_experiment("Existing Experiment")

        assert exp_id == "existing-exp-id"
        mock_mlflow.create_experiment.assert_not_called()

    def test_log_params_handles_long_values(self, mock_mlflow, mock_client):
        """log_params truncates long parameter values."""
        tracker = MLflowTracker(tracking_uri="http://test:5000")

        long_value = "x" * 600  # Over 500 char limit
        tracker.log_params({"short": "value", "long": long_value})

        # Should have logged both, with long value truncated
        calls = mock_mlflow.log_param.call_args_list
        assert len(calls) == 2

    def test_log_metrics_filters_non_numeric(self, mock_mlflow, mock_client):
        """log_metrics only logs numeric values."""
        tracker = MLflowTracker(tracking_uri="http://test:5000")

        tracker.log_metrics(
            {
                "accuracy": 0.95,
                "f1": 0.9,
                "confusion_matrix": [[1, 2], [3, 4]],  # Non-numeric
                "is_valid": True,  # Boolean
            }
        )

        # Should only log accuracy and f1
        calls = mock_mlflow.log_metric.call_args_list
        assert len(calls) == 2

    def test_log_model_result_creates_nested_run(self, mock_mlflow, mock_client):
        """log_model_result creates a nested run for the model."""
        mock_run = MagicMock()
        mock_run.info.run_id = "run-123"
        mock_mlflow.start_run.return_value.__enter__ = MagicMock(return_value=mock_run)
        mock_mlflow.start_run.return_value.__exit__ = MagicMock(return_value=None)

        tracker = MLflowTracker(tracking_uri="http://test:5000")

        result = {
            "model_name": "Test Model",
            "model_family": "sklearn",
            "hyperparameters": {"n_estimators": 100},
            "metrics": {"accuracy": 0.95},
            "training_duration_seconds": 1.5,
            "inference_latency_ms": 0.05,
            "global_score": 0.94,
        }

        run_id = tracker.log_model_result(
            result=result,
            experiment_id="exp-123",
            parent_run_id="parent-123",
        )

        assert run_id == "run-123"

    def test_log_model_result_with_error(self, mock_mlflow, mock_client):
        """log_model_result handles results with errors."""
        mock_run = MagicMock()
        mock_run.info.run_id = "run-123"
        mock_mlflow.start_run.return_value.__enter__ = MagicMock(return_value=mock_run)
        mock_mlflow.start_run.return_value.__exit__ = MagicMock(return_value=None)

        tracker = MLflowTracker(tracking_uri="http://test:5000")

        result = {
            "model_name": "Failed Model",
            "model_family": "sklearn",
            "metrics": {},
            "error_message": "Training failed: out of memory",
        }

        run_id = tracker.log_model_result(
            result=result,
            experiment_id="exp-123",
        )

        # Should set error tag
        mock_mlflow.set_tag.assert_any_call("error", "true")

    def test_log_experiment_summary(self, mock_mlflow, mock_client):
        """log_experiment_summary logs overall experiment metrics."""
        mock_run = MagicMock()
        mock_run.info.run_id = "summary-run-123"
        mock_mlflow.start_run.return_value.__enter__ = MagicMock(return_value=mock_run)
        mock_mlflow.start_run.return_value.__exit__ = MagicMock(return_value=None)

        tracker = MLflowTracker(tracking_uri="http://test:5000")

        run_id = tracker.log_experiment_summary(
            experiment_id="exp-123",
            run_name="Test Summary",
            total_models=5,
            successful_models=4,
            best_model_name="XGBoost",
            best_model_score=0.95,
            recommendation="Use XGBoost",
            duration_seconds=120.5,
        )

        assert run_id == "summary-run-123"

    def test_health_check_returns_true_when_healthy(self, mock_mlflow, mock_client):
        """health_check returns True when MLflow is reachable."""
        mock_client_instance = MagicMock()
        mock_client.return_value = mock_client_instance
        mock_client_instance.search_experiments.return_value = []

        tracker = MLflowTracker(tracking_uri="http://test:5000")

        assert tracker.health_check() is True

    def test_health_check_returns_false_on_error(self, mock_mlflow, mock_client):
        """health_check returns False when MLflow is unreachable."""
        mock_client_instance = MagicMock()
        mock_client.return_value = mock_client_instance
        mock_client_instance.search_experiments.side_effect = Exception("Connection refused")

        tracker = MLflowTracker(tracking_uri="http://test:5000")

        assert tracker.health_check() is False


class TestGetTracker:
    """Tests for get_tracker function."""

    def test_get_tracker_returns_instance(self):
        """get_tracker returns an MLflowTracker instance."""
        with patch("backend.app.experiment_layer.tracking.mlflow_client.MlflowClient"):
            tracker = get_tracker()
            assert isinstance(tracker, MLflowTracker)
