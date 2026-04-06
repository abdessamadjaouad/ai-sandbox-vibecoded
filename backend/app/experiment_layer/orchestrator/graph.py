# backend/app/experiment_layer/orchestrator/graph.py
"""
LangGraph experiment orchestrator — StateGraph definition.

Implements the experiment execution flow as a directed graph:

  [validate_inputs]
        ↓
  [select_models]        ← uses model catalogue + constraint filter
        ↓
  [prepare_data]         ← load versioned dataset splits
        ↓
  [run_experiments]      ← train/evaluate each model
        ↓
  [collect_artefacts]    ← merge results
        ↓
  [evaluate]             ← compute KPIs (placeholder for Phase 4)
        ↓
  [score_and_rank]       ← weighted global score + ranking
        ↓
  [generate_report]      ← create summary + recommendation
        ↓
  [audit_log]            ← immutable governance record
"""

from datetime import datetime
from typing import Any, Literal
import hashlib
import json

import pandas as pd
from langgraph.graph import StateGraph, END

from backend.app.models.experiment import ExperimentStatus, TaskType
from backend.app.experiment_layer.orchestrator.state import (
    ExperimentState,
    ModelResult,
    add_audit_entry,
)
from backend.app.experiment_layer.orchestrator.catalogue import get_catalogue
from backend.app.experiment_layer.runners.tabular_ml import TabularMLRunner

import structlog

logger = structlog.get_logger(__name__)


# =============================================================================
# Graph Nodes
# =============================================================================


def validate_inputs(state: ExperimentState) -> ExperimentState:
    """
    Validate experiment inputs and configuration.

    Checks:
    - Dataset ID is provided
    - Target column is set (for supervised learning)
    - At least one model is configured
    - Task type is valid

    Args:
        state: Current experiment state

    Returns:
        Updated state with status and audit entry
    """
    logger.info("validate_inputs", run_id=state.get("run_id"))

    errors = []

    # Check dataset
    if not state.get("dataset_id"):
        errors.append("dataset_id is required")

    # Check target column for supervised learning
    experiment_type = state.get("experiment_type")
    if experiment_type == "tabular_ml" and not state.get("target_column"):
        errors.append("target_column is required for tabular ML experiments")

    # Check models config
    models_config = state.get("models_config", [])
    if not models_config:
        errors.append("At least one model must be configured")

    # Check task type for tabular ML
    if experiment_type == "tabular_ml" and not state.get("task_type"):
        errors.append("task_type is required for tabular ML experiments")

    if errors:
        state = add_audit_entry(state, "validate_inputs", "validation_failed", {"errors": errors})
        return {
            **state,
            "status": ExperimentStatus.FAILED.value,
            "error_message": "; ".join(errors),
        }

    state = add_audit_entry(state, "validate_inputs", "validation_passed")
    return {**state, "status": ExperimentStatus.VALIDATING.value}


def select_models(state: ExperimentState) -> ExperimentState:
    """
    Select and validate models from configuration.

    Filters models based on:
    - Task type compatibility
    - Constraint limits (max_models)
    - Enabled flag

    If no models explicitly configured, uses defaults from catalogue.

    Args:
        state: Current experiment state

    Returns:
        Updated state with validated models_config
    """
    logger.info("select_models", run_id=state.get("run_id"))

    task_type_str = state.get("task_type")
    task_type = TaskType(task_type_str) if task_type_str else None
    models_config = state.get("models_config", [])
    constraints = state.get("constraints") or {}
    catalogue = get_catalogue()

    # If no models configured, get defaults
    if not models_config and task_type:
        max_models = constraints.get("max_models", 5)
        models_config = catalogue.get_default_models_for_task(task_type, max_models)
        logger.info(
            "using_default_models",
            task_type=task_type.value,
            num_models=len(models_config),
        )

    # Filter enabled models only
    enabled_models = [m for m in models_config if m.get("enabled", True)]

    # Apply max_models constraint
    max_models = constraints.get("max_models")
    if max_models and len(enabled_models) > max_models:
        enabled_models = enabled_models[:max_models]

    # Validate each model exists in catalogue
    valid_models = []
    for model_config in enabled_models:
        model_name = model_config.get("name")
        if catalogue.get(model_name):
            valid_models.append(model_config)
        else:
            logger.warning("model_not_in_catalogue", model_name=model_name)

    state = add_audit_entry(
        state,
        "select_models",
        "models_selected",
        {"selected_count": len(valid_models), "model_names": [m["name"] for m in valid_models]},
    )

    return {**state, "models_config": valid_models}


def prepare_data(state: ExperimentState) -> ExperimentState:
    """
    Load and prepare dataset for training.

    This node is a placeholder that expects data to be provided
    externally (via the data_loader dependency injection).
    In the full implementation, it would:
    - Load data from MinIO using dataset_version_id
    - Split into train/val/test if not already split
    - Compute data hash for reproducibility

    Args:
        state: Current experiment state

    Returns:
        Updated state with data info
    """
    logger.info("prepare_data", run_id=state.get("run_id"))

    # For MVP, data is injected externally before graph execution
    # This node validates that data is present

    train_data = state.get("train_data")
    if not train_data:
        state = add_audit_entry(state, "prepare_data", "data_missing")
        return {
            **state,
            "status": ExperimentStatus.FAILED.value,
            "error_message": "Training data not provided",
        }

    # Compute data hash for reproducibility tracking
    data_info = {
        "dataset_id": state.get("dataset_id"),
        "dataset_version_id": state.get("dataset_version_id"),
        "target_column": state.get("target_column"),
        "feature_columns": state.get("feature_columns"),
        "random_seed": state.get("random_seed"),
    }
    data_hash = hashlib.sha256(json.dumps(data_info, sort_keys=True).encode()).hexdigest()[:16]

    state = add_audit_entry(
        state,
        "prepare_data",
        "data_prepared",
        {"data_hash": data_hash},
    )

    return {
        **state,
        "status": ExperimentStatus.PREPARING.value,
        "data_hash": data_hash,
    }


def run_experiments(state: ExperimentState) -> ExperimentState:
    """
    Execute model training and evaluation.

    Runs each configured model through the TabularMLRunner,
    collecting results for later scoring.

    Args:
        state: Current experiment state with data loaded

    Returns:
        Updated state with results list
    """
    logger.info("run_experiments", run_id=state.get("run_id"))

    task_type_str = state.get("task_type")
    task_type = TaskType(task_type_str) if task_type_str else TaskType.CLASSIFICATION
    models_config = state.get("models_config", [])
    random_seed = state.get("random_seed", 42)

    # Get data from state (injected externally)
    train_data = state.get("train_data")
    val_data = state.get("val_data")
    test_data = state.get("test_data")
    target_column = state.get("target_column")
    feature_columns = state.get("feature_columns")

    if not train_data or not target_column:
        return {
            **state,
            "status": ExperimentStatus.FAILED.value,
            "error_message": "Training data or target column missing",
        }

    # Convert data dicts back to DataFrames
    X_train, y_train = _extract_features_target(train_data, target_column, feature_columns)
    X_val, y_val = _extract_features_target(val_data, target_column, feature_columns) if val_data else (None, None)
    X_test, y_test = _extract_features_target(test_data, target_column, feature_columns) if test_data else (None, None)

    # Run models
    runner = TabularMLRunner(random_seed=random_seed)
    results = runner.run_multiple_models(
        models_config=models_config,
        task_type=task_type,
        X_train=X_train,
        y_train=y_train,
        X_val=X_val,
        y_val=y_val,
        X_test=X_test,
        y_test=y_test,
    )

    successful = [r for r in results if not r.get("error_message")]
    failed = [r for r in results if r.get("error_message")]

    state = add_audit_entry(
        state,
        "run_experiments",
        "experiments_completed",
        {
            "total": len(results),
            "successful": len(successful),
            "failed": len(failed),
        },
    )

    return {
        **state,
        "status": ExperimentStatus.RUNNING.value,
        "results": results,
    }


def collect_artefacts(state: ExperimentState) -> ExperimentState:
    """
    Collect and organize experiment artefacts.

    In full implementation, this would:
    - Save trained models to MinIO
    - Store predictions, feature importance plots
    - Update artefact paths in results

    For MVP, this is a pass-through that marks artefacts as collected.

    Args:
        state: Current experiment state

    Returns:
        Updated state with artefact paths
    """
    logger.info("collect_artefacts", run_id=state.get("run_id"))

    # MVP: Just mark artefacts as collected
    # Full implementation would save to MinIO here

    artefacts = []
    run_id = state.get("run_id")
    for result in state.get("results", []):
        model_name = result.get("model_name", "unknown").replace(" ", "_").lower()
        artefact_path = f"s3://sandbox/{run_id}/{model_name}/model.joblib"
        artefacts.append(artefact_path)

    state = add_audit_entry(
        state,
        "collect_artefacts",
        "artefacts_collected",
        {"artefact_count": len(artefacts)},
    )

    return {**state, "artefacts": artefacts}


def evaluate(state: ExperimentState) -> ExperimentState:
    """
    Compute evaluation KPIs from results.

    For tabular ML, extracts metrics from model results.
    For LLM/RAG/Agent (Phase 4), would call DeepEval/RAGAS here.

    Args:
        state: Current experiment state

    Returns:
        Updated state with kpi_scores
    """
    logger.info("evaluate", run_id=state.get("run_id"))

    kpi_scores = {}
    for result in state.get("results", []):
        model_name = result.get("model_name")
        metrics = result.get("metrics", {})
        if model_name and metrics:
            # Filter to numeric metrics only
            kpi_scores[model_name] = {
                k: v for k, v in metrics.items() if isinstance(v, (int, float)) and not isinstance(v, bool)
            }

    state = add_audit_entry(
        state,
        "evaluate",
        "kpis_computed",
        {"models_evaluated": len(kpi_scores)},
    )

    return {
        **state,
        "status": ExperimentStatus.EVALUATING.value,
        "kpi_scores": kpi_scores,
    }


def score_and_rank(state: ExperimentState) -> ExperimentState:
    """
    Compute global scores and rank models.

    Uses weighted scoring formula (configurable per use case):
      global_score = Σ (normalised_metric_i × weight_i)

    Default weights for tabular ML:
    - accuracy/r2: 40%
    - precision/mae: 20%
    - recall/rmse: 20%
    - f1/mse: 20%

    Args:
        state: Current experiment state

    Returns:
        Updated state with global_scores and ranked results
    """
    logger.info("score_and_rank", run_id=state.get("run_id"))

    task_type_str = state.get("task_type")
    kpi_scores = state.get("kpi_scores", {})
    constraints = state.get("constraints") or {}

    # Define default weights based on task type
    if task_type_str == TaskType.CLASSIFICATION.value:
        weights = {
            "accuracy": 0.4,
            "f1": 0.3,
            "precision": 0.15,
            "recall": 0.15,
        }
        higher_is_better = True
    else:  # Regression
        weights = {
            "r2": 0.4,
            "mae": 0.2,
            "rmse": 0.2,
            "mse": 0.2,
        }
        higher_is_better = {"r2": True, "mae": False, "rmse": False, "mse": False}

    # Compute global scores
    global_scores = {}
    for model_name, metrics in kpi_scores.items():
        score = 0.0
        total_weight = 0.0

        for metric_name, weight in weights.items():
            if metric_name in metrics:
                value = metrics[metric_name]

                # Normalize: for metrics where lower is better, invert
                if isinstance(higher_is_better, dict):
                    if not higher_is_better.get(metric_name, True):
                        # Invert by using 1/(1+value) for metrics like MAE, RMSE
                        value = 1.0 / (1.0 + value)

                score += value * weight
                total_weight += weight

        if total_weight > 0:
            global_scores[model_name] = score / total_weight

    # Apply constraint penalties
    min_accuracy = constraints.get("min_accuracy")
    if min_accuracy and task_type_str == TaskType.CLASSIFICATION.value:
        for model_name in list(global_scores.keys()):
            accuracy = kpi_scores.get(model_name, {}).get("accuracy", 0)
            if accuracy < min_accuracy:
                global_scores[model_name] *= 0.5  # Penalty

    # Rank models
    ranked_models = sorted(global_scores.items(), key=lambda x: x[1], reverse=True)

    # Update results with global scores and ranks
    results = state.get("results", [])
    updated_results = []
    for result in results:
        model_name = result.get("model_name")
        result_copy = dict(result)
        result_copy["global_score"] = global_scores.get(model_name)

        # Find rank
        for rank, (ranked_name, _) in enumerate(ranked_models, 1):
            if ranked_name == model_name:
                result_copy["rank"] = rank
                break

        updated_results.append(result_copy)

    state = add_audit_entry(
        state,
        "score_and_rank",
        "models_ranked",
        {"ranking": [name for name, _ in ranked_models]},
    )

    return {
        **state,
        "results": updated_results,
        "global_scores": global_scores,
    }


def generate_report(state: ExperimentState) -> ExperimentState:
    """
    Generate experiment summary and recommendation.

    Creates a plain-language recommendation for the user.

    Args:
        state: Current experiment state

    Returns:
        Updated state with recommendation
    """
    logger.info("generate_report", run_id=state.get("run_id"))

    results = state.get("results", [])
    global_scores = state.get("global_scores", {})
    task_type_str = state.get("task_type")

    # Find best model
    best_model = None
    best_score = -1
    for result in results:
        model_name = result.get("model_name")
        score = global_scores.get(model_name, 0)
        if score > best_score and not result.get("error_message"):
            best_score = score
            best_model = model_name

    # Generate recommendation
    if best_model:
        task_label = "classification" if task_type_str == TaskType.CLASSIFICATION.value else "regression"

        # Get key metric for the best model
        best_metrics = next(
            (r.get("metrics", {}) for r in results if r.get("model_name") == best_model),
            {},
        )

        if task_type_str == TaskType.CLASSIFICATION.value:
            key_metric = best_metrics.get("accuracy", 0)
            metric_name = "accuracy"
        else:
            key_metric = best_metrics.get("r2", 0)
            metric_name = "R²"

        recommendation = (
            f"For this {task_label} task, we recommend **{best_model}** "
            f"with a {metric_name} of {key_metric:.2%}. "
            f"This model achieved the highest overall score ({best_score:.3f}) "
            f"across all evaluation metrics."
        )
    else:
        recommendation = (
            "No models completed successfully. Please check the error messages and verify your dataset configuration."
        )

    state = add_audit_entry(
        state,
        "generate_report",
        "report_generated",
        {"best_model": best_model, "recommendation_length": len(recommendation)},
    )

    return {**state, "recommendation": recommendation}


def audit_log(state: ExperimentState) -> ExperimentState:
    """
    Finalize audit trail and mark experiment complete.

    This is the terminal node that:
    - Marks the experiment as completed
    - Records the final timestamp
    - Ensures audit trail is complete

    Args:
        state: Current experiment state

    Returns:
        Final state with completed status
    """
    logger.info("audit_log", run_id=state.get("run_id"))

    # Preserve failed status if already set (from validation or other failures)
    current_status = state.get("status")
    if current_status == ExperimentStatus.FAILED.value:
        final_status = ExperimentStatus.FAILED.value
    else:
        # Check for any failures in results
        results = state.get("results", [])
        failed_count = sum(1 for r in results if r.get("error_message"))

        if failed_count == len(results) and results:
            final_status = ExperimentStatus.FAILED.value
        else:
            final_status = ExperimentStatus.COMPLETED.value

    state = add_audit_entry(
        state,
        "audit_log",
        "experiment_finalized",
        {
            "final_status": final_status,
            "total_audit_entries": len(state.get("audit_trail", [])) + 1,
        },
    )

    return {
        **state,
        "status": final_status,
        "completed_at": datetime.utcnow().isoformat(),
    }


# =============================================================================
# Helper Functions
# =============================================================================


def _extract_features_target(
    data: dict[str, Any] | None,
    target_column: str,
    feature_columns: list[str] | None,
) -> tuple[pd.DataFrame | None, pd.Series | None]:
    """
    Extract features and target from data dictionary.

    Args:
        data: Dictionary with 'data' key containing records
        target_column: Name of target column
        feature_columns: List of feature columns (None = all except target)

    Returns:
        Tuple of (X, y) DataFrames/Series
    """
    if not data:
        return None, None

    records = data.get("data", [])
    if not records:
        return None, None

    df = pd.DataFrame(records)

    if target_column not in df.columns:
        raise ValueError(f"Target column '{target_column}' not found in data")

    y = df[target_column]

    if feature_columns:
        X = df[feature_columns]
    else:
        X = df.drop(columns=[target_column])

    return X, y


def should_continue(state: ExperimentState) -> Literal["continue", "end"]:
    """
    Determine if graph should continue or end early.

    Args:
        state: Current experiment state

    Returns:
        "continue" to proceed, "end" to terminate
    """
    status = state.get("status")
    if status == ExperimentStatus.FAILED.value:
        return "end"
    return "continue"


# =============================================================================
# Graph Construction
# =============================================================================


def create_experiment_graph() -> StateGraph:
    """
    Create the LangGraph StateGraph for experiment orchestration.

    Graph topology:
        validate_inputs → select_models → prepare_data → run_experiments →
        collect_artefacts → evaluate → score_and_rank → generate_report → audit_log

    Returns:
        Compiled StateGraph ready for execution
    """
    # Create graph with state schema
    graph = StateGraph(ExperimentState)

    # Add nodes
    graph.add_node("validate_inputs", validate_inputs)
    graph.add_node("select_models", select_models)
    graph.add_node("prepare_data", prepare_data)
    graph.add_node("run_experiments", run_experiments)
    graph.add_node("collect_artefacts", collect_artefacts)
    graph.add_node("evaluate", evaluate)
    graph.add_node("score_and_rank", score_and_rank)
    graph.add_node("generate_report", generate_report)
    graph.add_node("audit_log", audit_log)

    # Set entry point
    graph.set_entry_point("validate_inputs")

    # Add edges with conditional routing for early termination
    graph.add_conditional_edges(
        "validate_inputs",
        should_continue,
        {"continue": "select_models", "end": "audit_log"},
    )
    graph.add_edge("select_models", "prepare_data")
    graph.add_conditional_edges(
        "prepare_data",
        should_continue,
        {"continue": "run_experiments", "end": "audit_log"},
    )
    graph.add_edge("run_experiments", "collect_artefacts")
    graph.add_edge("collect_artefacts", "evaluate")
    graph.add_edge("evaluate", "score_and_rank")
    graph.add_edge("score_and_rank", "generate_report")
    graph.add_edge("generate_report", "audit_log")
    graph.add_edge("audit_log", END)

    return graph.compile()


# Create a singleton graph instance
_graph = None


def get_experiment_graph() -> StateGraph:
    """
    Get the compiled experiment graph (singleton).

    Returns:
        Compiled StateGraph
    """
    global _graph
    if _graph is None:
        _graph = create_experiment_graph()
    return _graph
