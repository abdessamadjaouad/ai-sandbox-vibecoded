# backend/app/api/evaluation/routes.py
"""
Evaluation API routes.

Provides endpoints for computing metrics, scoring models, and generating reports.
"""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db_session
from backend.app.models.experiment import (
    Experiment,
    ExperimentResult,
    ExperimentStatus,
    TaskType,
)
from backend.app.evaluation_layer.metrics import (
    MetricsCalculator,
    ClassificationMetrics,
    RegressionMetrics,
)
from backend.app.evaluation_layer.scoring import (
    WeightedScorer,
    ScoringConfig,
    ConstraintChecker,
    ConstraintConfig,
)
from backend.app.evaluation_layer.reports import ReportGenerator, ReportConfig

import structlog

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/evaluation", tags=["evaluation"])


# =============================================================================
# Request/Response Schemas
# =============================================================================


class ComputeMetricsRequest(BaseModel):
    """Request for computing metrics."""

    task_type: TaskType = Field(..., description="Classification or regression")
    y_true: list[Any] = Field(..., description="Ground truth values")
    y_pred: list[Any] = Field(..., description="Predicted values")
    y_prob: list[list[float]] | None = Field(None, description="Predicted probabilities (classification only)")
    class_labels: list[str] | None = Field(None, description="Class labels for classification")


class ComputeMetricsResponse(BaseModel):
    """Response with computed metrics."""

    task_type: TaskType
    metrics: dict[str, Any]
    support: int


class ScoreModelsRequest(BaseModel):
    """Request for scoring multiple models."""

    task_type: TaskType = Field(..., description="Task type for metric mapping")
    results: list[dict[str, Any]] = Field(
        ...,
        description="List of model results with metrics, latency, cost",
    )
    weights: dict[str, float] | None = Field(
        None,
        description="Custom weights (performance, robustness, latency, cost)",
    )
    constraints: ConstraintConfig | None = Field(
        None,
        description="Constraint configuration",
    )


class ScoreModelsResponse(BaseModel):
    """Response with scoring results."""

    scores: list[dict[str, Any]]
    recommendation: str
    best_model: str | None
    best_score: float | None
    passed_count: int
    failed_count: int


class GenerateReportRequest(BaseModel):
    """Request for report generation."""

    experiment_id: uuid.UUID = Field(..., description="Experiment ID")
    config: ReportConfig | None = Field(None, description="Report configuration")


class GenerateReportResponse(BaseModel):
    """Response with generated report."""

    experiment_id: uuid.UUID
    experiment_name: str
    markdown_content: str
    summary: str
    recommendation: str
    best_model: str | None
    best_score: float | None


# =============================================================================
# Metrics Endpoints
# =============================================================================


@router.post("/metrics/compute", response_model=ComputeMetricsResponse)
async def compute_metrics(
    request: ComputeMetricsRequest,
) -> ComputeMetricsResponse:
    """
    Compute metrics for predictions.

    Given ground truth and predictions, computes comprehensive metrics
    based on the task type (classification or regression).

    Args:
        request: Metrics computation request

    Returns:
        Computed metrics
    """
    calculator = MetricsCalculator(class_labels=request.class_labels)

    try:
        result = calculator.compute(
            task_type=request.task_type,
            y_true=request.y_true,
            y_pred=request.y_pred,
            y_prob=request.y_prob,
        )

        metrics_dict = result.model_dump()
        support = metrics_dict.pop("support", len(request.y_true))

        logger.info(
            "metrics_computed_via_api",
            task_type=request.task_type.value,
            support=support,
        )

        return ComputeMetricsResponse(
            task_type=request.task_type,
            metrics=metrics_dict,
            support=support,
        )

    except Exception as e:
        logger.error("metrics_computation_failed", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/metrics/available")
async def list_available_metrics(
    task_type: TaskType = Query(..., description="Task type"),
) -> dict[str, Any]:
    """
    List available metrics for a task type.

    Args:
        task_type: Classification or regression

    Returns:
        Dict with metric names
    """
    calculator = MetricsCalculator()
    metrics = calculator.get_all_metric_names(task_type)
    primary = calculator.get_primary_metric(task_type)

    return {
        "metrics": metrics,
        "primary_metric": primary,
        "task_type": task_type.value,
    }


# =============================================================================
# Scoring Endpoints
# =============================================================================


@router.post("/score", response_model=ScoreModelsResponse)
async def score_models(
    request: ScoreModelsRequest,
) -> ScoreModelsResponse:
    """
    Score and rank multiple models.

    Computes weighted global scores and applies constraints to determine
    the best model recommendation.

    Args:
        request: Scoring request with model results

    Returns:
        Scoring results with recommendation
    """
    # Build scoring config
    scoring_config = ScoringConfig()
    if request.weights:
        scoring_config.weights = request.weights

    # Initialize scorer and constraint checker
    scorer = WeightedScorer(config=scoring_config, task_type=request.task_type)

    # Check constraints if configured
    if request.constraints:
        checker = ConstraintChecker(config=request.constraints)
        constraint_results = checker.check_multiple(request.results)

        # Mark invalid models
        for result, constraint in zip(request.results, constraint_results):
            if not constraint.passed:
                result["constraint_violations"] = constraint.violations
    else:
        constraint_results = None

    # Score models
    scoring_results = scorer.score_multiple(request.results)

    # Apply constraint violations to scoring results
    if constraint_results:
        for score_result, constraint in zip(scoring_results, constraint_results):
            if not constraint.passed:
                score_result.is_valid = False
                score_result.constraint_violations = constraint.violations

    # Generate recommendation
    recommendation = scorer.get_recommendation(scoring_results)

    # Find best model
    valid_results = [r for r in scoring_results if r.is_valid and r.rank is not None]
    best = min(valid_results, key=lambda r: r.rank or float("inf")) if valid_results else None

    passed = sum(1 for r in scoring_results if r.is_valid)
    failed = len(scoring_results) - passed

    logger.info(
        "models_scored_via_api",
        total=len(scoring_results),
        passed=passed,
        best_model=best.model_name if best else None,
    )

    return ScoreModelsResponse(
        scores=[r.model_dump() for r in scoring_results],
        recommendation=recommendation,
        best_model=best.model_name if best else None,
        best_score=best.global_score if best else None,
        passed_count=passed,
        failed_count=failed,
    )


@router.get("/score/weights/default")
async def get_default_weights() -> dict[str, float]:
    """
    Get default scoring weights.

    Returns:
        Default weight configuration
    """
    return {
        "performance": 0.40,
        "robustness": 0.20,
        "latency": 0.20,
        "cost": 0.20,
    }


# =============================================================================
# Report Endpoints
# =============================================================================


@router.post("/report/generate", response_model=GenerateReportResponse)
async def generate_report(
    request: GenerateReportRequest,
    session: AsyncSession = Depends(get_db_session),
) -> GenerateReportResponse:
    """
    Generate an evaluation report for an experiment.

    Creates a comprehensive Markdown report with model comparison,
    metrics, and recommendations.

    Args:
        request: Report generation request
        session: Database session

    Returns:
        Generated report
    """
    # Load experiment
    result = await session.execute(select(Experiment).where(Experiment.id == request.experiment_id))
    experiment = result.scalar_one_or_none()

    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    if experiment.status not in [ExperimentStatus.COMPLETED, ExperimentStatus.FAILED]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot generate report for experiment in {experiment.status.value} status",
        )

    # Load results
    results_query = await session.execute(
        select(ExperimentResult)
        .where(ExperimentResult.experiment_id == request.experiment_id)
        .order_by(ExperimentResult.rank.nullslast())
    )
    results = results_query.scalars().all()

    if not results:
        raise HTTPException(status_code=400, detail="No results found for experiment")

    # Build scoring results from experiment results
    from backend.app.evaluation_layer.scoring.scorer import ScoringResult

    scoring_results = []
    for r in results:
        scoring_results.append(
            ScoringResult(
                model_name=r.model_name,
                global_score=r.global_score or 0.0,
                rank=r.rank,
                raw_metrics=r.metrics or {},
                is_valid=r.error_message is None,
                constraint_violations=[r.error_message] if r.error_message else [],
            )
        )

    # Generate report
    generator = ReportGenerator(config=request.config or ReportConfig())

    duration = None
    if experiment.started_at and experiment.completed_at:
        duration = (experiment.completed_at - experiment.started_at).total_seconds()

    report = generator.generate(
        experiment_id=experiment.id,
        experiment_name=experiment.name,
        task_type=experiment.task_type,
        status=experiment.status,
        scoring_results=scoring_results,
        duration_seconds=duration,
        constraints_config=experiment.constraints,
    )

    logger.info(
        "report_generated_via_api",
        experiment_id=str(experiment.id),
        best_model=report.best_model,
    )

    return GenerateReportResponse(
        experiment_id=report.experiment_id,
        experiment_name=report.experiment_name,
        markdown_content=report.markdown_content,
        summary=report.summary,
        recommendation=report.recommendation,
        best_model=report.best_model,
        best_score=report.best_score,
    )


@router.get(
    "/report/{experiment_id}/markdown",
    response_class=PlainTextResponse,
)
async def get_report_markdown(
    experiment_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
) -> str:
    """
    Get experiment report as raw Markdown.

    Convenience endpoint that returns plain Markdown text
    suitable for rendering or downloading.

    Args:
        experiment_id: Experiment UUID
        session: Database session

    Returns:
        Markdown report content
    """
    request = GenerateReportRequest(experiment_id=experiment_id)
    response = await generate_report(request, session)
    return response.markdown_content


# =============================================================================
# Experiment-Specific Endpoints
# =============================================================================


@router.get("/experiment/{experiment_id}/scores")
async def get_experiment_scores(
    experiment_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """
    Get scoring breakdown for an experiment.

    Returns detailed scoring information including category scores
    and constraint validation.

    Args:
        experiment_id: Experiment UUID
        session: Database session

    Returns:
        Scoring breakdown
    """
    # Load experiment and results
    exp_result = await session.execute(select(Experiment).where(Experiment.id == experiment_id))
    experiment = exp_result.scalar_one_or_none()

    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    results_query = await session.execute(
        select(ExperimentResult)
        .where(ExperimentResult.experiment_id == experiment_id)
        .order_by(ExperimentResult.rank.nullslast())
    )
    results = results_query.scalars().all()

    # Build response
    models = []
    for r in results:
        models.append(
            {
                "model_name": r.model_name,
                "global_score": r.global_score,
                "rank": r.rank,
                "metrics": r.metrics,
                "training_duration_seconds": r.training_duration_seconds,
                "inference_latency_ms": r.inference_latency_ms,
                "error_message": r.error_message,
            }
        )

    # Find best
    valid = [m for m in models if m["error_message"] is None and m["rank"] is not None]
    best = min(valid, key=lambda m: m["rank"] or float("inf")) if valid else None

    return {
        "experiment_id": str(experiment_id),
        "experiment_name": experiment.name,
        "task_type": experiment.task_type.value,
        "status": experiment.status.value,
        "total_models": len(models),
        "passed_models": len(valid),
        "best_model": best["model_name"] if best else None,
        "best_score": best["global_score"] if best else None,
        "models": models,
    }
