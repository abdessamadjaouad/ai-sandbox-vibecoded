# tests/unit/test_experiment_layer/test_state.py
"""Tests for experiment state schema."""

import uuid
from datetime import datetime

import pytest

from backend.app.experiment_layer.orchestrator.state import (
    ExperimentState,
    create_initial_state,
    add_audit_entry,
    ModelResult,
    AuditEntry,
)
from backend.app.models.experiment import ExperimentType, TaskType


class TestExperimentState:
    """Tests for ExperimentState TypedDict and helper functions."""

    def test_create_initial_state_returns_valid_state(self):
        """create_initial_state returns a state with all required fields."""
        experiment_id = uuid.uuid4()
        dataset_id = uuid.uuid4()

        state = create_initial_state(
            experiment_id=experiment_id,
            experiment_name="Test Experiment",
            experiment_type=ExperimentType.TABULAR_ML,
            task_type=TaskType.CLASSIFICATION,
            dataset_id=dataset_id,
            dataset_version_id=None,
            target_column="target",
            feature_columns=["feature1", "feature2"],
            models_config=[{"name": "Random Forest Classifier", "enabled": True}],
            constraints={"max_models": 5},
            random_seed=42,
            owner_id="user123",
        )

        assert state["run_id"] is not None
        assert state["experiment_id"] == str(experiment_id)
        assert state["experiment_name"] == "Test Experiment"
        assert state["experiment_type"] == "tabular_ml"
        assert state["task_type"] == "classification"
        assert state["status"] == "pending"
        assert state["dataset_id"] == str(dataset_id)
        assert state["target_column"] == "target"
        assert state["feature_columns"] == ["feature1", "feature2"]
        assert len(state["models_config"]) == 1
        assert state["random_seed"] == 42
        assert state["results"] == []
        assert state["audit_trail"] == []
        assert state["started_at"] is not None
        assert state["owner_id"] == "user123"

    def test_create_initial_state_with_minimal_config(self):
        """create_initial_state works with minimal configuration."""
        state = create_initial_state(
            experiment_id=uuid.uuid4(),
            experiment_name="Minimal",
            experiment_type=ExperimentType.TABULAR_ML,
            task_type=None,
            dataset_id=uuid.uuid4(),
            dataset_version_id=None,
            target_column=None,
            feature_columns=None,
            models_config=[],
            constraints=None,
            random_seed=0,
        )

        assert state["task_type"] is None
        assert state["target_column"] is None
        assert state["feature_columns"] is None
        assert state["constraints"] is None

    def test_add_audit_entry_appends_to_trail(self):
        """add_audit_entry correctly appends audit entries."""
        state = create_initial_state(
            experiment_id=uuid.uuid4(),
            experiment_name="Test",
            experiment_type=ExperimentType.TABULAR_ML,
            task_type=TaskType.CLASSIFICATION,
            dataset_id=uuid.uuid4(),
            dataset_version_id=None,
            target_column="target",
            feature_columns=None,
            models_config=[],
            constraints=None,
            random_seed=42,
            owner_id="user1",
        )

        # Initially empty
        assert len(state["audit_trail"]) == 0

        # Add first entry
        state = add_audit_entry(
            state,
            node="validate_inputs",
            action="validation_passed",
            details={"input_count": 5},
        )

        assert len(state["audit_trail"]) == 1
        assert state["audit_trail"][0]["node"] == "validate_inputs"
        assert state["audit_trail"][0]["action"] == "validation_passed"
        assert state["audit_trail"][0]["details"]["input_count"] == 5
        assert state["audit_trail"][0]["user_id"] == "user1"

        # Add second entry
        state = add_audit_entry(state, "select_models", "models_selected")

        assert len(state["audit_trail"]) == 2
        assert state["audit_trail"][1]["node"] == "select_models"

    def test_add_audit_entry_without_details(self):
        """add_audit_entry works without details parameter."""
        state = create_initial_state(
            experiment_id=uuid.uuid4(),
            experiment_name="Test",
            experiment_type=ExperimentType.TABULAR_ML,
            task_type=TaskType.CLASSIFICATION,
            dataset_id=uuid.uuid4(),
            dataset_version_id=None,
            target_column="target",
            feature_columns=None,
            models_config=[],
            constraints=None,
            random_seed=42,
        )

        state = add_audit_entry(state, "test_node", "test_action")

        assert state["audit_trail"][0]["details"] == {}


class TestModelResult:
    """Tests for ModelResult TypedDict."""

    def test_model_result_structure(self):
        """ModelResult has expected structure."""
        result: ModelResult = {
            "model_name": "XGBoost Classifier",
            "model_family": "xgboost",
            "model_config": {"name": "XGBoost Classifier"},
            "hyperparameters": {"n_estimators": 100},
            "metrics": {"accuracy": 0.95, "f1": 0.94},
            "global_score": 0.945,
            "rank": 1,
            "training_duration_seconds": 1.5,
            "inference_latency_ms": 0.05,
            "artefact_path": "s3://sandbox/run1/xgboost.joblib",
            "mlflow_run_id": "abc123",
            "error_message": None,
            "predictions": [0, 1, 1, 0],
        }

        assert result["model_name"] == "XGBoost Classifier"
        assert result["metrics"]["accuracy"] == 0.95
        assert result["rank"] == 1

    def test_model_result_with_error(self):
        """ModelResult can represent failed model runs."""
        result: ModelResult = {
            "model_name": "Failed Model",
            "model_family": "sklearn",
            "model_config": {},
            "hyperparameters": {},
            "metrics": {},
            "global_score": None,
            "rank": None,
            "training_duration_seconds": None,
            "inference_latency_ms": None,
            "artefact_path": None,
            "mlflow_run_id": None,
            "error_message": "Training failed: out of memory",
            "predictions": None,
        }

        assert result["error_message"] is not None
        assert result["metrics"] == {}
