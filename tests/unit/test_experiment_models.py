# tests/unit/test_experiment_models.py
"""Tests for experiment models and schemas."""

import uuid
from datetime import datetime

import pytest
from pydantic import ValidationError

from backend.app.models.experiment import (
    ExperimentCreate,
    ExperimentRead,
    ExperimentResultRead,
    ExperimentSummary,
    ModelConfig,
    ExperimentConstraints,
    ExperimentStatus,
    ExperimentType,
    TaskType,
    ModelFamily,
)


class TestExperimentEnums:
    """Tests for experiment enums."""

    def test_experiment_status_values(self):
        """ExperimentStatus has expected values."""
        assert ExperimentStatus.PENDING.value == "pending"
        assert ExperimentStatus.RUNNING.value == "running"
        assert ExperimentStatus.COMPLETED.value == "completed"
        assert ExperimentStatus.FAILED.value == "failed"

    def test_experiment_type_values(self):
        """ExperimentType has expected values."""
        assert ExperimentType.TABULAR_ML.value == "tabular_ml"
        assert ExperimentType.NLP.value == "nlp"
        assert ExperimentType.LLM.value == "llm"
        assert ExperimentType.RAG.value == "rag"
        assert ExperimentType.AGENT.value == "agent"

    def test_task_type_values(self):
        """TaskType has expected values."""
        assert TaskType.CLASSIFICATION.value == "classification"
        assert TaskType.REGRESSION.value == "regression"
        assert TaskType.CLUSTERING.value == "clustering"

    def test_model_family_values(self):
        """ModelFamily has expected values."""
        assert ModelFamily.SKLEARN.value == "sklearn"
        assert ModelFamily.XGBOOST.value == "xgboost"
        assert ModelFamily.LIGHTGBM.value == "lightgbm"


class TestModelConfig:
    """Tests for ModelConfig schema."""

    def test_model_config_valid(self):
        """ModelConfig accepts valid configuration."""
        config = ModelConfig(
            name="Random Forest",
            family=ModelFamily.SKLEARN,
            class_name="RandomForestClassifier",
            hyperparameters={"n_estimators": 100},
        )

        assert config.name == "Random Forest"
        assert config.family == ModelFamily.SKLEARN
        assert config.enabled is True  # Default

    def test_model_config_defaults(self):
        """ModelConfig has correct defaults."""
        config = ModelConfig(
            name="Test",
            family=ModelFamily.SKLEARN,
            class_name="TestClass",
        )

        assert config.hyperparameters == {}
        assert config.enabled is True


class TestExperimentConstraints:
    """Tests for ExperimentConstraints schema."""

    def test_constraints_valid(self):
        """ExperimentConstraints accepts valid values."""
        constraints = ExperimentConstraints(
            max_training_time_seconds=60.0,
            max_models=5,
            min_accuracy=0.8,
            max_latency_ms=100.0,
        )

        assert constraints.max_models == 5
        assert constraints.min_accuracy == 0.8

    def test_constraints_min_accuracy_validation(self):
        """ExperimentConstraints validates min_accuracy range."""
        # Valid
        constraints = ExperimentConstraints(min_accuracy=0.5)
        assert constraints.min_accuracy == 0.5

        # Invalid - too high
        with pytest.raises(ValidationError):
            ExperimentConstraints(min_accuracy=1.5)

        # Invalid - negative
        with pytest.raises(ValidationError):
            ExperimentConstraints(min_accuracy=-0.1)


class TestExperimentCreate:
    """Tests for ExperimentCreate schema."""

    def test_experiment_create_valid(self):
        """ExperimentCreate accepts valid data."""
        exp = ExperimentCreate(
            name="Test Experiment",
            description="A test experiment",
            experiment_type=ExperimentType.TABULAR_ML,
            task_type=TaskType.CLASSIFICATION,
            dataset_id=uuid.uuid4(),
            target_column="target",
        )

        assert exp.name == "Test Experiment"
        assert exp.experiment_type == ExperimentType.TABULAR_ML

    def test_experiment_create_minimal(self):
        """ExperimentCreate works with minimal required fields."""
        exp = ExperimentCreate(
            name="Minimal",
            dataset_id=uuid.uuid4(),
        )

        assert exp.name == "Minimal"
        assert exp.experiment_type == ExperimentType.TABULAR_ML  # Default
        assert exp.models == []  # Default
        assert exp.random_seed == 42  # Default

    def test_experiment_create_empty_name_fails(self):
        """ExperimentCreate rejects empty name."""
        with pytest.raises(ValidationError):
            ExperimentCreate(
                name="",
                dataset_id=uuid.uuid4(),
            )


class TestExperimentRead:
    """Tests for ExperimentRead schema."""

    def test_experiment_read_from_attributes(self):
        """ExperimentRead can be created from model attributes."""

        class MockExperiment:
            id = uuid.uuid4()
            name = "Test"
            description = "Description"
            experiment_type = ExperimentType.TABULAR_ML
            task_type = TaskType.CLASSIFICATION
            status = ExperimentStatus.COMPLETED
            dataset_id = uuid.uuid4()
            dataset_version_id = None
            target_column = "target"
            feature_columns = ["f1", "f2"]
            models_config = {"models": []}
            constraints = None
            mlflow_experiment_id = "mlflow-123"
            mlflow_run_id = "run-456"
            random_seed = 42
            started_at = datetime.utcnow()
            completed_at = datetime.utcnow()
            error_message = None
            created_at = datetime.utcnow()
            updated_at = datetime.utcnow()

        exp = ExperimentRead.model_validate(MockExperiment())

        assert exp.name == "Test"
        assert exp.status == ExperimentStatus.COMPLETED


class TestExperimentResultRead:
    """Tests for ExperimentResultRead schema."""

    def test_experiment_result_read_structure(self):
        """ExperimentResultRead has correct structure."""

        class MockResult:
            id = uuid.uuid4()
            experiment_id = uuid.uuid4()
            model_name = "XGBoost"
            model_family = ModelFamily.XGBOOST
            model_config = {"name": "XGBoost"}
            hyperparameters = {"n_estimators": 100}
            metrics = {"accuracy": 0.95}
            global_score = 0.94
            rank = 1
            training_duration_seconds = 1.5
            inference_latency_ms = 0.05
            artefact_path = "s3://bucket/model.joblib"
            mlflow_run_id = "run-123"
            error_message = None
            created_at = datetime.utcnow()

        result = ExperimentResultRead.model_validate(MockResult())

        assert result.model_name == "XGBoost"
        assert result.rank == 1


class TestExperimentSummary:
    """Tests for ExperimentSummary schema."""

    def test_experiment_summary_structure(self):
        """ExperimentSummary has correct structure."""
        summary = ExperimentSummary(
            experiment_id=uuid.uuid4(),
            experiment_name="Test",
            status=ExperimentStatus.COMPLETED,
            total_models=5,
            successful_models=4,
            failed_models=1,
            best_model_name="XGBoost",
            best_model_score=0.95,
            recommendation="Use XGBoost",
            duration_seconds=120.5,
        )

        assert summary.total_models == 5
        assert summary.best_model_name == "XGBoost"
