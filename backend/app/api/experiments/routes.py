# backend/app/api/experiments/routes.py
"""
Experiments API routes.

Provides endpoints for creating, running, and managing experiments.
"""

import uuid
from datetime import datetime
from typing import Any

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db_session as get_session, async_session_factory
from backend.app.models.experiment import (
    Experiment,
    ExperimentResult,
    ExperimentCreate,
    ExperimentRead,
    ExperimentResultRead,
    ExperimentListResponse,
    ExperimentSummary,
    ExperimentStatus,
    ExperimentType,
    TaskType,
    ModelConfig,
)
from backend.app.models.dataset import Dataset, DatasetVersion
from backend.app.experiment_layer.orchestrator.state import create_initial_state, ExperimentState
from backend.app.experiment_layer.orchestrator.graph import get_experiment_graph
from backend.app.experiment_layer.orchestrator.catalogue import get_catalogue
from backend.app.experiment_layer.tracking.mlflow_client import get_tracker
from backend.app.data_layer.storage import get_storage_client

import structlog

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/experiments", tags=["experiments"])


# =============================================================================
# Catalogue Endpoints
# =============================================================================


@router.get("/catalogue/models")
async def list_available_models(
    task_type: TaskType | None = Query(None, description="Filter by task type"),
) -> list[dict[str, Any]]:
    """
    List all available models in the catalogue.

    Args:
        task_type: Optional filter by task type (classification/regression)

    Returns:
        List of model definitions
    """
    catalogue = get_catalogue()

    if task_type:
        models = catalogue.list_by_task_type(task_type)
    else:
        models = catalogue.list_all()

    return [model.to_dict() for model in models]


@router.get("/catalogue/defaults/{task_type}")
async def get_default_models(
    task_type: TaskType,
    max_models: int = Query(5, ge=1, le=20),
) -> list[dict[str, Any]]:
    """
    Get recommended default models for a task type.

    Args:
        task_type: Task type (classification/regression)
        max_models: Maximum number of models to return

    Returns:
        List of recommended model configurations
    """
    catalogue = get_catalogue()
    return catalogue.get_default_models_for_task(task_type, max_models)


# =============================================================================
# Experiment CRUD
# =============================================================================


@router.post("", response_model=ExperimentRead, status_code=201)
async def create_experiment(
    experiment_in: ExperimentCreate,
    session: AsyncSession = Depends(get_session),
) -> ExperimentRead:
    """
    Create a new experiment.

    Args:
        experiment_in: Experiment creation data
        session: Database session

    Returns:
        Created experiment
    """
    # Verify dataset exists
    dataset_result = await session.execute(select(Dataset).where(Dataset.id == experiment_in.dataset_id))
    dataset = dataset_result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # Verify dataset version if provided
    if experiment_in.dataset_version_id:
        version_result = await session.execute(
            select(DatasetVersion).where(
                DatasetVersion.id == experiment_in.dataset_version_id,
                DatasetVersion.dataset_id == experiment_in.dataset_id,
            )
        )
        version = version_result.scalar_one_or_none()
        if not version:
            raise HTTPException(status_code=404, detail="Dataset version not found")

    # Convert models list to JSON-serializable dict
    models_config = {
        "models": [model.model_dump() if isinstance(model, ModelConfig) else model for model in experiment_in.models]
    }

    # Create experiment record
    experiment = Experiment(
        name=experiment_in.name,
        description=experiment_in.description,
        experiment_type=experiment_in.experiment_type,
        task_type=experiment_in.task_type,
        dataset_id=experiment_in.dataset_id,
        dataset_version_id=experiment_in.dataset_version_id,
        target_column=experiment_in.target_column,
        feature_columns=experiment_in.feature_columns,
        models_config=models_config,
        constraints=experiment_in.constraints.model_dump() if experiment_in.constraints else None,
        random_seed=experiment_in.random_seed,
    )

    session.add(experiment)
    await session.commit()
    await session.refresh(experiment)

    logger.info("experiment_created", experiment_id=str(experiment.id), name=experiment.name)

    return ExperimentRead.model_validate(experiment)


@router.get("", response_model=ExperimentListResponse)
async def list_experiments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: ExperimentStatus | None = None,
    experiment_type: ExperimentType | None = None,
    session: AsyncSession = Depends(get_session),
) -> ExperimentListResponse:
    """
    List experiments with pagination and filtering.

    Args:
        page: Page number
        page_size: Items per page
        status: Filter by status
        experiment_type: Filter by type
        session: Database session

    Returns:
        Paginated list of experiments
    """
    query = select(Experiment)
    count_query = select(func.count(Experiment.id))

    if status:
        query = query.where(Experiment.status == status)
        count_query = count_query.where(Experiment.status == status)

    if experiment_type:
        query = query.where(Experiment.experiment_type == experiment_type)
        count_query = count_query.where(Experiment.experiment_type == experiment_type)

    # Get total count
    total_result = await session.execute(count_query)
    total = total_result.scalar() or 0

    # Get paginated results
    query = query.order_by(Experiment.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await session.execute(query)
    experiments = result.scalars().all()

    return ExperimentListResponse(
        items=[ExperimentRead.model_validate(exp) for exp in experiments],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{experiment_id}", response_model=ExperimentRead)
async def get_experiment(
    experiment_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> ExperimentRead:
    """
    Get experiment by ID.

    Args:
        experiment_id: Experiment UUID
        session: Database session

    Returns:
        Experiment details
    """
    result = await session.execute(select(Experiment).where(Experiment.id == experiment_id))
    experiment = result.scalar_one_or_none()

    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    return ExperimentRead.model_validate(experiment)


@router.get("/{experiment_id}/results", response_model=list[ExperimentResultRead])
async def get_experiment_results(
    experiment_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> list[ExperimentResultRead]:
    """
    Get results for an experiment.

    Args:
        experiment_id: Experiment UUID
        session: Database session

    Returns:
        List of experiment results
    """
    # Verify experiment exists
    exp_result = await session.execute(select(Experiment).where(Experiment.id == experiment_id))
    if not exp_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Experiment not found")

    # Get results
    result = await session.execute(
        select(ExperimentResult)
        .where(ExperimentResult.experiment_id == experiment_id)
        .order_by(ExperimentResult.rank.nullslast())
    )
    results = result.scalars().all()

    return [ExperimentResultRead.model_validate(r) for r in results]


@router.get("/{experiment_id}/summary", response_model=ExperimentSummary)
async def get_experiment_summary(
    experiment_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> ExperimentSummary:
    """
    Get summary of experiment results.

    Args:
        experiment_id: Experiment UUID
        session: Database session

    Returns:
        Experiment summary with recommendation
    """
    # Get experiment
    exp_result = await session.execute(select(Experiment).where(Experiment.id == experiment_id))
    experiment = exp_result.scalar_one_or_none()

    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    # Get results
    results_query = await session.execute(
        select(ExperimentResult)
        .where(ExperimentResult.experiment_id == experiment_id)
        .order_by(ExperimentResult.rank.nullslast())
    )
    results = results_query.scalars().all()

    successful = [r for r in results if not r.error_message]
    failed = [r for r in results if r.error_message]

    # Find best model
    best_model = None
    best_score = None
    if successful:
        best = min(successful, key=lambda r: r.rank or float("inf"))
        best_model = best.model_name
        best_score = best.global_score

    # Calculate duration
    duration = None
    if experiment.started_at and experiment.completed_at:
        duration = (experiment.completed_at - experiment.started_at).total_seconds()

    # Build recommendation
    recommendation = None
    if experiment.status == ExperimentStatus.COMPLETED and best_model:
        recommendation = f"Based on the evaluation, {best_model} is recommended with a score of {best_score:.3f}."
    elif experiment.status == ExperimentStatus.FAILED:
        recommendation = f"Experiment failed: {experiment.error_message}"

    return ExperimentSummary(
        experiment_id=experiment.id,
        experiment_name=experiment.name,
        status=experiment.status,
        total_models=len(results),
        successful_models=len(successful),
        failed_models=len(failed),
        best_model_name=best_model,
        best_model_score=best_score,
        recommendation=recommendation,
        duration_seconds=duration,
    )


# =============================================================================
# Experiment Execution
# =============================================================================


@router.post("/{experiment_id}/run", response_model=ExperimentRead)
async def run_experiment(
    experiment_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
) -> ExperimentRead:
    """
    Start running an experiment.

    Executes the experiment asynchronously in the background.

    Args:
        experiment_id: Experiment UUID
        background_tasks: FastAPI background tasks
        session: Database session

    Returns:
        Updated experiment with running status
    """
    # Get experiment
    result = await session.execute(select(Experiment).where(Experiment.id == experiment_id))
    experiment = result.scalar_one_or_none()

    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    # Check status
    if experiment.status not in [ExperimentStatus.PENDING, ExperimentStatus.FAILED]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot run experiment in {experiment.status.value} status",
        )

    # Update status to running
    experiment.status = ExperimentStatus.RUNNING
    experiment.started_at = datetime.utcnow()
    await session.commit()
    await session.refresh(experiment)

    # Add background task to run experiment
    # Note: In production, this would use Celery or similar
    # For MVP, we use FastAPI background tasks
    background_tasks.add_task(
        _execute_experiment,
        experiment_id=experiment.id,
    )

    logger.info("experiment_started", experiment_id=str(experiment.id))

    return ExperimentRead.model_validate(experiment)


async def _execute_experiment(experiment_id: uuid.UUID) -> None:
    """
    Execute an experiment (background task).

    This is the main execution function that:
    1. Loads the experiment and dataset
    2. Prepares the data
    3. Runs the LangGraph orchestrator
    4. Saves results to database
    5. Logs to MLflow

    Args:
        experiment_id: Experiment UUID
    """
    from backend.app.core.database import async_session_factory

    async with async_session_factory() as session:
        try:
            # Load experiment
            result = await session.execute(select(Experiment).where(Experiment.id == experiment_id))
            experiment = result.scalar_one_or_none()

            if not experiment:
                logger.error("experiment_not_found", experiment_id=str(experiment_id))
                return

            # Load dataset version
            if experiment.dataset_version_id:
                version_result = await session.execute(
                    select(DatasetVersion).where(DatasetVersion.id == experiment.dataset_version_id)
                )
                version = version_result.scalar_one_or_none()
            else:
                # Get latest version
                version_result = await session.execute(
                    select(DatasetVersion)
                    .where(DatasetVersion.dataset_id == experiment.dataset_id)
                    .order_by(DatasetVersion.version.desc())
                    .limit(1)
                )
                version = version_result.scalar_one_or_none()

            if not version:
                raise ValueError("No dataset version found")

            # Load data from MinIO
            storage = get_storage_client()
            train_data = await _load_data_from_storage(storage, version.train_path)
            val_data = await _load_data_from_storage(storage, version.val_path) if version.val_path else None
            test_data = await _load_data_from_storage(storage, version.test_path) if version.test_path else None

            # Extract models config
            models_config = experiment.models_config.get("models", [])

            # Create initial state
            state = create_initial_state(
                experiment_id=experiment.id,
                experiment_name=experiment.name,
                experiment_type=experiment.experiment_type,
                task_type=experiment.task_type,
                dataset_id=experiment.dataset_id,
                dataset_version_id=version.id,
                target_column=experiment.target_column,
                feature_columns=experiment.feature_columns,
                models_config=models_config,
                constraints=experiment.constraints,
                random_seed=experiment.random_seed,
            )

            # Inject data into state
            state["train_data"] = train_data
            state["val_data"] = val_data
            state["test_data"] = test_data
            state["dataset_version"] = version.version

            # Run the graph
            graph = get_experiment_graph()
            final_state = graph.invoke(state)

            # Save results to database
            await _save_experiment_results(session, experiment, final_state)

            # Log to MLflow
            await _log_to_mlflow(experiment, final_state)

            logger.info(
                "experiment_completed",
                experiment_id=str(experiment_id),
                status=final_state.get("status"),
            )

        except Exception as e:
            logger.error(
                "experiment_execution_failed",
                experiment_id=str(experiment_id),
                error=str(e),
            )
            # Update experiment status
            experiment.status = ExperimentStatus.FAILED
            experiment.error_message = str(e)
            experiment.completed_at = datetime.utcnow()
            await session.commit()


async def _load_data_from_storage(storage, path: str) -> dict[str, Any]:
    """Load data from MinIO and return as dict."""
    # Extract bucket and key from path
    # Path format: s3://bucket/key or bucket/key
    if path.startswith("s3://"):
        path = path[5:]

    parts = path.split("/", 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid path format: {path}")

    bucket, key = parts

    # Download file
    data_bytes = storage.download_file(bucket, key)

    # Parse based on extension
    if key.endswith(".parquet"):
        import io

        df = pd.read_parquet(io.BytesIO(data_bytes))
    elif key.endswith(".csv"):
        import io

        df = pd.read_csv(io.BytesIO(data_bytes))
    else:
        raise ValueError(f"Unsupported file format: {key}")

    return {"data": df.to_dict(orient="records"), "columns": list(df.columns)}


async def _save_experiment_results(
    session: AsyncSession,
    experiment: Experiment,
    final_state: ExperimentState,
) -> None:
    """Save experiment results to database."""
    from backend.app.models.experiment import ModelFamily

    # Update experiment
    experiment.status = ExperimentStatus(final_state.get("status", ExperimentStatus.FAILED.value))
    experiment.completed_at = datetime.utcnow()
    experiment.error_message = final_state.get("error_message")
    experiment.mlflow_run_id = final_state.get("mlflow_run_id")

    # Save individual results
    for result in final_state.get("results", []):
        exp_result = ExperimentResult(
            experiment_id=experiment.id,
            model_name=result.get("model_name", "Unknown"),
            model_family=ModelFamily(result.get("model_family", "sklearn")),
            model_config=result.get("model_config", {}),
            hyperparameters=result.get("hyperparameters"),
            metrics=result.get("metrics", {}),
            global_score=result.get("global_score"),
            rank=result.get("rank"),
            training_duration_seconds=result.get("training_duration_seconds"),
            inference_latency_ms=result.get("inference_latency_ms"),
            artefact_path=result.get("artefact_path"),
            mlflow_run_id=result.get("mlflow_run_id"),
            error_message=result.get("error_message"),
        )
        session.add(exp_result)

    await session.commit()


async def _log_to_mlflow(experiment: Experiment, final_state: ExperimentState) -> None:
    """Log experiment to MLflow."""
    try:
        tracker = get_tracker()

        # Create/get MLflow experiment
        mlflow_exp_id = tracker.get_or_create_experiment(f"ai-sandbox/{experiment.name}")

        # Log summary
        results = final_state.get("results", [])
        successful = [r for r in results if not r.get("error_message")]

        best_model = None
        best_score = None
        global_scores = final_state.get("global_scores", {})
        if global_scores:
            best_model = max(global_scores, key=global_scores.get)
            best_score = global_scores[best_model]

        duration = None
        if final_state.get("started_at") and final_state.get("completed_at"):
            from datetime import datetime

            start = datetime.fromisoformat(final_state["started_at"])
            end = datetime.fromisoformat(final_state["completed_at"])
            duration = (end - start).total_seconds()

        parent_run_id = tracker.log_experiment_summary(
            experiment_id=mlflow_exp_id,
            run_name=experiment.name,
            total_models=len(results),
            successful_models=len(successful),
            best_model_name=best_model,
            best_model_score=best_score,
            recommendation=final_state.get("recommendation"),
            duration_seconds=duration,
        )

        # Log individual model results as nested runs
        for result in results:
            tracker.log_model_result(
                result=result,
                experiment_id=mlflow_exp_id,
                parent_run_id=parent_run_id,
            )

    except Exception as e:
        logger.warning("mlflow_logging_failed", error=str(e))


@router.delete("/{experiment_id}", status_code=204)
async def delete_experiment(
    experiment_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> None:
    """
    Delete an experiment and its results.

    Args:
        experiment_id: Experiment UUID
        session: Database session
    """
    result = await session.execute(select(Experiment).where(Experiment.id == experiment_id))
    experiment = result.scalar_one_or_none()

    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    # Don't allow deleting running experiments
    if experiment.status == ExperimentStatus.RUNNING:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete a running experiment",
        )

    await session.delete(experiment)
    await session.commit()

    logger.info("experiment_deleted", experiment_id=str(experiment_id))
