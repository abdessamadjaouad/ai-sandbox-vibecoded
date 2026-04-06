# tests/unit/test_experiment_layer/test_runner.py
"""Tests for tabular ML runner."""

import numpy as np
import pandas as pd
import pytest

from backend.app.experiment_layer.runners.tabular_ml import TabularMLRunner
from backend.app.models.experiment import TaskType


class TestTabularMLRunner:
    """Tests for TabularMLRunner class."""

    @pytest.fixture
    def classification_data(self):
        """Create synthetic classification dataset."""
        np.random.seed(42)
        n_samples = 100
        X = pd.DataFrame(
            {
                "feature1": np.random.randn(n_samples),
                "feature2": np.random.randn(n_samples),
                "feature3": np.random.randn(n_samples),
            }
        )
        y = pd.Series(np.random.randint(0, 2, n_samples), name="target")
        return X, y

    @pytest.fixture
    def regression_data(self):
        """Create synthetic regression dataset."""
        np.random.seed(42)
        n_samples = 100
        X = pd.DataFrame(
            {
                "feature1": np.random.randn(n_samples),
                "feature2": np.random.randn(n_samples),
            }
        )
        y = pd.Series(X["feature1"] * 2 + X["feature2"] + np.random.randn(n_samples) * 0.1, name="target")
        return X, y

    def test_train_and_evaluate_classification(self, classification_data):
        """train_and_evaluate works for classification."""
        X, y = classification_data
        X_train, X_val = X[:80], X[80:]
        y_train, y_val = y[:80], y[80:]

        runner = TabularMLRunner(random_seed=42)
        model_config = {
            "name": "Random Forest Classifier",
            "family": "sklearn",
            "hyperparameters": {"n_estimators": 10},
        }

        result = runner.train_and_evaluate(
            model_config=model_config,
            task_type=TaskType.CLASSIFICATION,
            X_train=X_train,
            y_train=y_train,
            X_val=X_val,
            y_val=y_val,
        )

        assert result["model_name"] == "Random Forest Classifier"
        assert result["error_message"] is None
        assert "accuracy" in result["metrics"]
        assert "precision" in result["metrics"]
        assert "recall" in result["metrics"]
        assert "f1" in result["metrics"]
        assert result["training_duration_seconds"] is not None
        assert result["training_duration_seconds"] > 0
        assert result["inference_latency_ms"] is not None

    def test_train_and_evaluate_regression(self, regression_data):
        """train_and_evaluate works for regression."""
        X, y = regression_data
        X_train, X_val = X[:80], X[80:]
        y_train, y_val = y[:80], y[80:]

        runner = TabularMLRunner(random_seed=42)
        model_config = {
            "name": "Random Forest Regressor",
            "family": "sklearn",
            "hyperparameters": {"n_estimators": 10},
        }

        result = runner.train_and_evaluate(
            model_config=model_config,
            task_type=TaskType.REGRESSION,
            X_train=X_train,
            y_train=y_train,
            X_val=X_val,
            y_val=y_val,
        )

        assert result["model_name"] == "Random Forest Regressor"
        assert result["error_message"] is None
        assert "mse" in result["metrics"]
        assert "rmse" in result["metrics"]
        assert "mae" in result["metrics"]
        assert "r2" in result["metrics"]

    def test_train_and_evaluate_with_test_set(self, classification_data):
        """train_and_evaluate computes test metrics when test set provided."""
        X, y = classification_data
        X_train, X_val, X_test = X[:60], X[60:80], X[80:]
        y_train, y_val, y_test = y[:60], y[60:80], y[80:]

        runner = TabularMLRunner(random_seed=42)
        model_config = {
            "name": "Logistic Regression",
            "family": "sklearn",
            "hyperparameters": {},
        }

        result = runner.train_and_evaluate(
            model_config=model_config,
            task_type=TaskType.CLASSIFICATION,
            X_train=X_train,
            y_train=y_train,
            X_val=X_val,
            y_val=y_val,
            X_test=X_test,
            y_test=y_test,
        )

        # Should have both val and test metrics
        assert "accuracy" in result["metrics"]  # Val metric
        assert "test_accuracy" in result["metrics"]  # Test metric

    def test_train_and_evaluate_handles_error(self, classification_data):
        """train_and_evaluate captures errors gracefully."""
        X, y = classification_data

        runner = TabularMLRunner(random_seed=42)
        model_config = {
            "name": "NonExistent Model",
            "family": "sklearn",
            "hyperparameters": {},
        }

        result = runner.train_and_evaluate(
            model_config=model_config,
            task_type=TaskType.CLASSIFICATION,
            X_train=X[:80],
            y_train=y[:80],
        )

        assert result["error_message"] is not None
        assert result["metrics"] == {}

    def test_train_and_evaluate_xgboost(self, classification_data):
        """train_and_evaluate works with XGBoost."""
        X, y = classification_data

        runner = TabularMLRunner(random_seed=42)
        model_config = {
            "name": "XGBoost Classifier",
            "family": "xgboost",
            "hyperparameters": {"n_estimators": 10, "verbosity": 0},
        }

        result = runner.train_and_evaluate(
            model_config=model_config,
            task_type=TaskType.CLASSIFICATION,
            X_train=X[:80],
            y_train=y[:80],
            X_val=X[80:],
            y_val=y[80:],
        )

        assert result["model_name"] == "XGBoost Classifier"
        assert result["error_message"] is None
        assert "accuracy" in result["metrics"]

    def test_train_and_evaluate_lightgbm(self, regression_data):
        """train_and_evaluate works with LightGBM."""
        X, y = regression_data

        runner = TabularMLRunner(random_seed=42)
        model_config = {
            "name": "LightGBM Regressor",
            "family": "lightgbm",
            "hyperparameters": {"n_estimators": 10, "verbosity": -1},
        }

        result = runner.train_and_evaluate(
            model_config=model_config,
            task_type=TaskType.REGRESSION,
            X_train=X[:80],
            y_train=y[:80],
            X_val=X[80:],
            y_val=y[80:],
        )

        assert result["model_name"] == "LightGBM Regressor"
        assert result["error_message"] is None
        assert "r2" in result["metrics"]

    def test_run_multiple_models(self, classification_data):
        """run_multiple_models trains all configured models."""
        X, y = classification_data

        runner = TabularMLRunner(random_seed=42)
        models_config = [
            {"name": "Random Forest Classifier", "hyperparameters": {"n_estimators": 5}, "enabled": True},
            {"name": "Logistic Regression", "hyperparameters": {}, "enabled": True},
            {"name": "Decision Tree Classifier", "hyperparameters": {}, "enabled": False},  # Disabled
        ]

        results = runner.run_multiple_models(
            models_config=models_config,
            task_type=TaskType.CLASSIFICATION,
            X_train=X[:80],
            y_train=y[:80],
            X_val=X[80:],
            y_val=y[80:],
        )

        # Should have 2 results (disabled model skipped)
        assert len(results) == 2

        model_names = [r["model_name"] for r in results]
        assert "Random Forest Classifier" in model_names
        assert "Logistic Regression" in model_names
        assert "Decision Tree Classifier" not in model_names

    def test_reproducibility_with_seed(self, classification_data):
        """Same seed produces same results."""
        X, y = classification_data
        model_config = {
            "name": "Random Forest Classifier",
            "hyperparameters": {"n_estimators": 5},
        }

        runner1 = TabularMLRunner(random_seed=42)
        result1 = runner1.train_and_evaluate(
            model_config=model_config,
            task_type=TaskType.CLASSIFICATION,
            X_train=X[:80],
            y_train=y[:80],
            X_val=X[80:],
            y_val=y[80:],
        )

        runner2 = TabularMLRunner(random_seed=42)
        result2 = runner2.train_and_evaluate(
            model_config=model_config,
            task_type=TaskType.CLASSIFICATION,
            X_train=X[:80],
            y_train=y[:80],
            X_val=X[80:],
            y_val=y[80:],
        )

        assert result1["metrics"]["accuracy"] == result2["metrics"]["accuracy"]

    def test_string_labels_classification(self):
        """train_and_evaluate handles string labels."""
        np.random.seed(42)
        n_samples = 100
        X = pd.DataFrame(
            {
                "feature1": np.random.randn(n_samples),
                "feature2": np.random.randn(n_samples),
            }
        )
        y = pd.Series(np.where(np.random.rand(n_samples) > 0.5, "yes", "no"))

        runner = TabularMLRunner(random_seed=42)
        model_config = {
            "name": "Random Forest Classifier",
            "hyperparameters": {"n_estimators": 5},
        }

        result = runner.train_and_evaluate(
            model_config=model_config,
            task_type=TaskType.CLASSIFICATION,
            X_train=X[:80],
            y_train=y[:80],
            X_val=X[80:],
            y_val=y[80:],
        )

        assert result["error_message"] is None
        assert "accuracy" in result["metrics"]
