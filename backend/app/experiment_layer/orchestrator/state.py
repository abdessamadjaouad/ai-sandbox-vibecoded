# backend/app/experiment_layer/orchestrator/state.py
"""
LangGraph state schema for experiment orchestration.

Defines the TypedDict that flows through all graph nodes.
This is the single source of truth during a run.
"""

import uuid
from datetime import datetime
from typing import Any, TypedDict

from backend.app.models.experiment import ExperimentStatus, ExperimentType, TaskType, ModelFamily


class ModelResult(TypedDict, total=False):
    """Result from training/evaluating a single model."""

    model_name: str
    model_family: str
    model_config: dict[str, Any]
    hyperparameters: dict[str, Any]
    metrics: dict[str, float]
    global_score: float | None
    rank: int | None
    training_duration_seconds: float | None
    inference_latency_ms: float | None
    artefact_path: str | None
    mlflow_run_id: str | None
    error_message: str | None
    predictions: list[Any] | None


class AuditEntry(TypedDict):
    """Single audit log entry for governance tracking."""

    timestamp: str
    node: str
    action: str
    details: dict[str, Any]
    user_id: str | None


class ExperimentState(TypedDict, total=False):
    """
    LangGraph state schema for experiment orchestration.

    This TypedDict flows through all graph nodes and represents
    the complete state of an experiment run.

    Attributes:
        run_id: Unique identifier for this experiment run
        experiment_id: Database ID of the experiment record
        experiment_name: Human-readable experiment name
        experiment_type: Type of experiment (tabular_ml, nlp, llm, rag, agent)
        task_type: ML task type (classification, regression, clustering)
        status: Current execution status
        error_message: Error details if status is FAILED

        dataset_id: ID of the dataset being used
        dataset_version_id: ID of the specific dataset version
        dataset_version: Version number
        target_column: Column name for target variable (supervised learning)
        feature_columns: List of feature column names (None = use all except target)

        models_config: List of model configurations to evaluate
        constraints: Execution constraints (max time, min accuracy, etc.)
        random_seed: Seed for reproducibility

        train_data: Training data (loaded during prepare_data)
        val_data: Validation data (optional)
        test_data: Test data (optional)
        data_hash: Hash of dataset + config for reproducibility tracking

        results: List of results from each model
        artefacts: Paths to stored artefacts (models, predictions, etc.)
        kpi_scores: Computed KPI scores per model
        global_scores: Weighted global scores per model
        recommendation: Final recommendation string

        mlflow_experiment_id: MLflow experiment ID
        mlflow_run_id: MLflow parent run ID

        audit_trail: List of audit entries for governance
        started_at: Timestamp when run started
        completed_at: Timestamp when run completed
    """

    # Identifiers
    run_id: str
    experiment_id: str
    experiment_name: str
    experiment_type: str
    task_type: str | None
    status: str
    error_message: str | None

    # Dataset configuration
    dataset_id: str
    dataset_version_id: str | None
    dataset_version: int | None
    target_column: str | None
    feature_columns: list[str] | None

    # Models and constraints
    models_config: list[dict[str, Any]]
    constraints: dict[str, Any] | None
    random_seed: int

    # Data (populated during prepare_data node)
    train_data: dict[str, Any] | None  # Serialized DataFrame info
    val_data: dict[str, Any] | None
    test_data: dict[str, Any] | None
    data_hash: str | None

    # Results (populated during run_experiments and evaluate nodes)
    results: list[ModelResult]
    artefacts: list[str]
    kpi_scores: dict[str, dict[str, float]]
    global_scores: dict[str, float]
    recommendation: str | None

    # Tracking
    mlflow_experiment_id: str | None
    mlflow_run_id: str | None

    # Governance
    audit_trail: list[AuditEntry]
    started_at: str | None
    completed_at: str | None
    owner_id: str | None


def create_initial_state(
    experiment_id: uuid.UUID,
    experiment_name: str,
    experiment_type: ExperimentType,
    task_type: TaskType | None,
    dataset_id: uuid.UUID,
    dataset_version_id: uuid.UUID | None,
    target_column: str | None,
    feature_columns: list[str] | None,
    models_config: list[dict[str, Any]],
    constraints: dict[str, Any] | None,
    random_seed: int,
    owner_id: str | None = None,
) -> ExperimentState:
    """
    Create initial experiment state for a new run.

    Args:
        experiment_id: Database ID of the experiment
        experiment_name: Human-readable name
        experiment_type: Type of experiment
        task_type: ML task type (for tabular experiments)
        dataset_id: ID of the dataset
        dataset_version_id: ID of the dataset version (optional)
        target_column: Target column name
        feature_columns: Feature column names
        models_config: List of model configurations
        constraints: Execution constraints
        random_seed: Random seed for reproducibility
        owner_id: ID of the user running the experiment

    Returns:
        Initialized ExperimentState ready for graph execution.
    """
    return ExperimentState(
        run_id=str(uuid.uuid4()),
        experiment_id=str(experiment_id),
        experiment_name=experiment_name,
        experiment_type=experiment_type.value,
        task_type=task_type.value if task_type else None,
        status=ExperimentStatus.PENDING.value,
        error_message=None,
        dataset_id=str(dataset_id),
        dataset_version_id=str(dataset_version_id) if dataset_version_id else None,
        dataset_version=None,
        target_column=target_column,
        feature_columns=feature_columns,
        models_config=models_config,
        constraints=constraints,
        random_seed=random_seed,
        train_data=None,
        val_data=None,
        test_data=None,
        data_hash=None,
        results=[],
        artefacts=[],
        kpi_scores={},
        global_scores={},
        recommendation=None,
        mlflow_experiment_id=None,
        mlflow_run_id=None,
        audit_trail=[],
        started_at=datetime.utcnow().isoformat(),
        completed_at=None,
        owner_id=owner_id,
    )


def add_audit_entry(
    state: ExperimentState,
    node: str,
    action: str,
    details: dict[str, Any] | None = None,
) -> ExperimentState:
    """
    Add an audit entry to the state's audit trail.

    Args:
        state: Current experiment state
        node: Name of the graph node
        action: Description of the action taken
        details: Additional details (will be masked for sensitive data)

    Returns:
        Updated state with new audit entry.
    """
    entry = AuditEntry(
        timestamp=datetime.utcnow().isoformat(),
        node=node,
        action=action,
        details=details or {},
        user_id=state.get("owner_id"),
    )
    audit_trail = list(state.get("audit_trail", []))
    audit_trail.append(entry)
    return {**state, "audit_trail": audit_trail}
