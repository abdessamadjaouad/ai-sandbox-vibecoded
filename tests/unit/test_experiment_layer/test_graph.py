# tests/unit/test_experiment_layer/test_graph.py
"""Tests for LangGraph experiment orchestrator."""

import uuid

import numpy as np
import pandas as pd
import pytest

from backend.app.experiment_layer.orchestrator.graph import (
    create_experiment_graph,
    get_experiment_graph,
    validate_inputs,
    select_models,
    prepare_data,
    run_experiments,
    evaluate,
    score_and_rank,
    generate_report,
    audit_log,
    should_continue,
    _extract_features_target,
)
from backend.app.experiment_layer.orchestrator.state import create_initial_state
from backend.app.models.experiment import ExperimentType, TaskType, ExperimentStatus


class TestGraphNodes:
    """Tests for individual graph nodes."""

    @pytest.fixture
    def basic_state(self):
        """Create a basic initial state for testing."""
        return create_initial_state(
            experiment_id=uuid.uuid4(),
            experiment_name="Test Experiment",
            experiment_type=ExperimentType.TABULAR_ML,
            task_type=TaskType.CLASSIFICATION,
            dataset_id=uuid.uuid4(),
            dataset_version_id=None,
            target_column="target",
            feature_columns=None,
            models_config=[{"name": "Random Forest Classifier", "enabled": True}],
            constraints=None,
            random_seed=42,
        )

    @pytest.fixture
    def classification_data(self):
        """Create synthetic classification data."""
        np.random.seed(42)
        n_samples = 100
        data = {
            "feature1": np.random.randn(n_samples).tolist(),
            "feature2": np.random.randn(n_samples).tolist(),
            "target": np.random.randint(0, 2, n_samples).tolist(),
        }
        return {"data": [dict(zip(data.keys(), vals)) for vals in zip(*data.values())]}

    def test_validate_inputs_passes_with_valid_config(self, basic_state):
        """validate_inputs passes with valid configuration."""
        result = validate_inputs(basic_state)

        assert result["status"] == ExperimentStatus.VALIDATING.value
        assert result["error_message"] is None
        assert len(result["audit_trail"]) == 1

    def test_validate_inputs_fails_without_dataset(self, basic_state):
        """validate_inputs fails when dataset_id is missing."""
        basic_state["dataset_id"] = None

        result = validate_inputs(basic_state)

        assert result["status"] == ExperimentStatus.FAILED.value
        assert "dataset_id" in result["error_message"]

    def test_validate_inputs_fails_without_target(self, basic_state):
        """validate_inputs fails when target_column is missing for tabular ML."""
        basic_state["target_column"] = None

        result = validate_inputs(basic_state)

        assert result["status"] == ExperimentStatus.FAILED.value
        assert "target_column" in result["error_message"]

    def test_validate_inputs_fails_without_models(self, basic_state):
        """validate_inputs fails when no models configured."""
        basic_state["models_config"] = []

        result = validate_inputs(basic_state)

        assert result["status"] == ExperimentStatus.FAILED.value
        assert "model" in result["error_message"].lower()

    def test_select_models_uses_configured_models(self, basic_state):
        """select_models keeps configured models."""
        basic_state["models_config"] = [
            {"name": "Random Forest Classifier", "enabled": True},
            {"name": "Logistic Regression", "enabled": True},
        ]

        result = select_models(basic_state)

        assert len(result["models_config"]) == 2

    def test_select_models_filters_disabled(self, basic_state):
        """select_models filters out disabled models."""
        basic_state["models_config"] = [
            {"name": "Random Forest Classifier", "enabled": True},
            {"name": "Logistic Regression", "enabled": False},
        ]

        result = select_models(basic_state)

        assert len(result["models_config"]) == 1
        assert result["models_config"][0]["name"] == "Random Forest Classifier"

    def test_select_models_applies_max_constraint(self, basic_state):
        """select_models respects max_models constraint."""
        basic_state["models_config"] = [
            {"name": "Random Forest Classifier", "enabled": True},
            {"name": "Logistic Regression", "enabled": True},
            {"name": "XGBoost Classifier", "enabled": True},
        ]
        basic_state["constraints"] = {"max_models": 2}

        result = select_models(basic_state)

        assert len(result["models_config"]) == 2

    def test_select_models_uses_defaults_when_empty(self, basic_state):
        """select_models gets default models when none configured."""
        basic_state["models_config"] = []

        result = select_models(basic_state)

        # Should have default models for classification
        assert len(result["models_config"]) > 0

    def test_prepare_data_with_data_present(self, basic_state, classification_data):
        """prepare_data succeeds when data is present."""
        basic_state["train_data"] = classification_data

        result = prepare_data(basic_state)

        assert result["status"] == ExperimentStatus.PREPARING.value
        assert result["data_hash"] is not None

    def test_prepare_data_fails_without_data(self, basic_state):
        """prepare_data fails when training data is missing."""
        basic_state["train_data"] = None

        result = prepare_data(basic_state)

        assert result["status"] == ExperimentStatus.FAILED.value
        assert "data" in result["error_message"].lower()

    def test_run_experiments_trains_models(self, basic_state, classification_data):
        """run_experiments trains all configured models."""
        basic_state["train_data"] = classification_data
        basic_state["val_data"] = classification_data  # Use same data for simplicity
        basic_state["models_config"] = [
            {"name": "Random Forest Classifier", "hyperparameters": {"n_estimators": 5}, "enabled": True},
        ]

        result = run_experiments(basic_state)

        assert result["status"] == ExperimentStatus.RUNNING.value
        assert len(result["results"]) == 1
        assert result["results"][0]["model_name"] == "Random Forest Classifier"
        assert "accuracy" in result["results"][0]["metrics"]

    def test_evaluate_extracts_kpis(self, basic_state):
        """evaluate extracts KPI scores from results."""
        basic_state["results"] = [
            {
                "model_name": "Model A",
                "metrics": {"accuracy": 0.9, "f1": 0.85},
            },
            {
                "model_name": "Model B",
                "metrics": {"accuracy": 0.8, "f1": 0.75},
            },
        ]

        result = evaluate(basic_state)

        assert "Model A" in result["kpi_scores"]
        assert "Model B" in result["kpi_scores"]
        assert result["kpi_scores"]["Model A"]["accuracy"] == 0.9

    def test_score_and_rank_ranks_models(self, basic_state):
        """score_and_rank computes global scores and ranks."""
        basic_state["results"] = [
            {"model_name": "Model A", "metrics": {"accuracy": 0.9, "f1": 0.85}},
            {"model_name": "Model B", "metrics": {"accuracy": 0.8, "f1": 0.75}},
        ]
        basic_state["kpi_scores"] = {
            "Model A": {"accuracy": 0.9, "f1": 0.85},
            "Model B": {"accuracy": 0.8, "f1": 0.75},
        }

        result = score_and_rank(basic_state)

        assert "Model A" in result["global_scores"]
        assert "Model B" in result["global_scores"]
        assert result["global_scores"]["Model A"] > result["global_scores"]["Model B"]

        # Check ranking in results
        model_a = next(r for r in result["results"] if r["model_name"] == "Model A")
        model_b = next(r for r in result["results"] if r["model_name"] == "Model B")
        assert model_a["rank"] < model_b["rank"]

    def test_generate_report_creates_recommendation(self, basic_state):
        """generate_report creates a recommendation string."""
        basic_state["results"] = [
            {"model_name": "Best Model", "metrics": {"accuracy": 0.95}},
            {"model_name": "Other Model", "metrics": {"accuracy": 0.85}},
        ]
        basic_state["global_scores"] = {"Best Model": 0.95, "Other Model": 0.85}

        result = generate_report(basic_state)

        assert result["recommendation"] is not None
        assert "Best Model" in result["recommendation"]

    def test_generate_report_handles_all_failed(self, basic_state):
        """generate_report handles case where all models failed."""
        basic_state["results"] = [
            {"model_name": "Failed Model", "metrics": {}, "error_message": "Error"},
        ]
        basic_state["global_scores"] = {}

        result = generate_report(basic_state)

        assert "failed" in result["recommendation"].lower() or "no models" in result["recommendation"].lower()

    def test_audit_log_marks_completed(self, basic_state):
        """audit_log marks experiment as completed."""
        basic_state["results"] = [
            {"model_name": "Model A", "metrics": {"accuracy": 0.9}},
        ]

        result = audit_log(basic_state)

        assert result["status"] == ExperimentStatus.COMPLETED.value
        assert result["completed_at"] is not None

    def test_audit_log_marks_failed_when_all_fail(self, basic_state):
        """audit_log marks experiment as failed when all models fail."""
        basic_state["results"] = [
            {"model_name": "Model A", "error_message": "Error 1"},
            {"model_name": "Model B", "error_message": "Error 2"},
        ]

        result = audit_log(basic_state)

        assert result["status"] == ExperimentStatus.FAILED.value


class TestShouldContinue:
    """Tests for the conditional routing function."""

    def test_should_continue_returns_continue_normally(self):
        """should_continue returns 'continue' when not failed."""
        state = {"status": ExperimentStatus.RUNNING.value}
        assert should_continue(state) == "continue"

    def test_should_continue_returns_end_on_failure(self):
        """should_continue returns 'end' when status is failed."""
        state = {"status": ExperimentStatus.FAILED.value}
        assert should_continue(state) == "end"


class TestExtractFeaturesTarget:
    """Tests for _extract_features_target helper."""

    def test_extract_features_target_basic(self):
        """_extract_features_target extracts X and y correctly."""
        data = {
            "data": [
                {"feature1": 1.0, "feature2": 2.0, "target": 0},
                {"feature1": 3.0, "feature2": 4.0, "target": 1},
            ]
        }

        X, y = _extract_features_target(data, "target", None)

        assert X.shape == (2, 2)
        assert len(y) == 2
        assert "target" not in X.columns

    def test_extract_features_target_with_feature_columns(self):
        """_extract_features_target uses specified feature columns."""
        data = {
            "data": [
                {"feature1": 1.0, "feature2": 2.0, "feature3": 5.0, "target": 0},
                {"feature1": 3.0, "feature2": 4.0, "feature3": 6.0, "target": 1},
            ]
        }

        X, y = _extract_features_target(data, "target", ["feature1", "feature2"])

        assert X.shape == (2, 2)
        assert list(X.columns) == ["feature1", "feature2"]

    def test_extract_features_target_returns_none_for_none_data(self):
        """_extract_features_target returns None for None input."""
        X, y = _extract_features_target(None, "target", None)

        assert X is None
        assert y is None


class TestGraphCreation:
    """Tests for graph creation and structure."""

    def test_create_experiment_graph_returns_compiled_graph(self):
        """create_experiment_graph returns a compiled graph."""
        graph = create_experiment_graph()

        # Should be callable (compiled graph)
        assert callable(graph.invoke)

    def test_get_experiment_graph_returns_singleton(self):
        """get_experiment_graph returns the same instance."""
        graph1 = get_experiment_graph()
        graph2 = get_experiment_graph()

        assert graph1 is graph2


class TestGraphExecution:
    """Integration tests for full graph execution."""

    def test_full_graph_execution_classification(self):
        """Full graph execution for classification task."""
        # Create synthetic data
        np.random.seed(42)
        n_samples = 100
        train_data = {
            "data": [
                {
                    "feature1": float(np.random.randn()),
                    "feature2": float(np.random.randn()),
                    "target": int(np.random.randint(0, 2)),
                }
                for _ in range(80)
            ]
        }
        val_data = {
            "data": [
                {
                    "feature1": float(np.random.randn()),
                    "feature2": float(np.random.randn()),
                    "target": int(np.random.randint(0, 2)),
                }
                for _ in range(20)
            ]
        }

        # Create initial state
        state = create_initial_state(
            experiment_id=uuid.uuid4(),
            experiment_name="Integration Test",
            experiment_type=ExperimentType.TABULAR_ML,
            task_type=TaskType.CLASSIFICATION,
            dataset_id=uuid.uuid4(),
            dataset_version_id=None,
            target_column="target",
            feature_columns=None,
            models_config=[
                {"name": "Random Forest Classifier", "hyperparameters": {"n_estimators": 5}, "enabled": True},
                {"name": "Logistic Regression", "hyperparameters": {}, "enabled": True},
            ],
            constraints=None,
            random_seed=42,
        )

        # Inject data
        state["train_data"] = train_data
        state["val_data"] = val_data

        # Run graph
        graph = create_experiment_graph()
        final_state = graph.invoke(state)

        # Verify final state
        assert final_state["status"] == ExperimentStatus.COMPLETED.value
        assert len(final_state["results"]) == 2
        assert final_state["recommendation"] is not None
        assert len(final_state["audit_trail"]) > 0
        assert final_state["completed_at"] is not None

        # Verify ranking
        ranked_results = sorted(final_state["results"], key=lambda r: r.get("rank", 999))
        assert ranked_results[0]["rank"] == 1

    def test_graph_early_termination_on_validation_failure(self):
        """Graph terminates early when validation fails."""
        state = create_initial_state(
            experiment_id=uuid.uuid4(),
            experiment_name="Bad Config",
            experiment_type=ExperimentType.TABULAR_ML,
            task_type=None,  # Missing task type - should fail validation
            dataset_id=uuid.uuid4(),
            dataset_version_id=None,
            target_column=None,  # Also missing
            feature_columns=None,
            models_config=[{"name": "Random Forest Classifier", "enabled": True}],
            constraints=None,
            random_seed=42,
        )

        graph = create_experiment_graph()
        final_state = graph.invoke(state)

        assert final_state["status"] == ExperimentStatus.FAILED.value
        assert final_state["error_message"] is not None
        # Should fail on task_type and target_column
        assert "task_type" in final_state["error_message"].lower() or "target" in final_state["error_message"].lower()
