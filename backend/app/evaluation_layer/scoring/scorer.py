# backend/app/evaluation_layer/scoring/scorer.py
"""
Weighted scoring system for model evaluation.

Computes global scores using configurable weights for different metric categories.
"""

from typing import Any

from pydantic import BaseModel, Field, field_validator

from backend.app.models.experiment import TaskType

import structlog

logger = structlog.get_logger(__name__)


# Default metric weights by category
DEFAULT_WEIGHTS = {
    "performance": 0.40,
    "robustness": 0.20,
    "latency": 0.20,
    "cost": 0.20,
}

# Metric to category mapping for classification
CLASSIFICATION_METRIC_CATEGORIES = {
    "accuracy": "performance",
    "balanced_accuracy": "performance",
    "precision": "performance",
    "recall": "performance",
    "f1": "performance",
    "auc_roc": "performance",
    "mcc": "performance",
    "cohen_kappa": "robustness",
}

# Metric to category mapping for regression
REGRESSION_METRIC_CATEGORIES = {
    "r2": "performance",
    "rmse": "performance",
    "mae": "performance",
    "mape": "performance",
    "explained_variance": "performance",
    "residual_std": "robustness",
}

# Higher is better for these metrics (others are lower is better)
HIGHER_IS_BETTER = {
    "accuracy",
    "balanced_accuracy",
    "precision",
    "recall",
    "f1",
    "auc_roc",
    "mcc",
    "cohen_kappa",
    "r2",
    "explained_variance",
}


class ScoringConfig(BaseModel):
    """Configuration for weighted scoring."""

    weights: dict[str, float] = Field(
        default_factory=lambda: DEFAULT_WEIGHTS.copy(),
        description="Weight for each category (performance, robustness, latency, cost)",
    )
    primary_metric: str | None = Field(
        None,
        description="Primary metric to use (overrides category weighting)",
    )
    normalize_metrics: bool = Field(
        True,
        description="Whether to normalize metrics to [0, 1] range",
    )
    custom_metric_weights: dict[str, float] | None = Field(
        None,
        description="Custom weights for specific metrics (overrides category)",
    )

    @field_validator("weights")
    @classmethod
    def validate_weights_sum(cls, v: dict[str, float]) -> dict[str, float]:
        """Ensure weights sum to 1.0 (within tolerance)."""
        total = sum(v.values())
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Weights must sum to 1.0, got {total}")
        return v


class ScoringResult(BaseModel):
    """Result of scoring computation."""

    model_name: str = Field(..., description="Model name")
    global_score: float = Field(..., description="Weighted global score [0, 1]")
    rank: int | None = Field(None, description="Rank among models (1 = best)")
    category_scores: dict[str, float] = Field(
        default_factory=dict,
        description="Score per category",
    )
    normalized_metrics: dict[str, float] = Field(
        default_factory=dict,
        description="Normalized metric values [0, 1]",
    )
    raw_metrics: dict[str, float] = Field(
        default_factory=dict,
        description="Original metric values",
    )
    is_valid: bool = Field(True, description="Whether model passed constraints")
    constraint_violations: list[str] = Field(
        default_factory=list,
        description="List of constraint violations",
    )


class WeightedScorer:
    """
    Compute weighted global scores for model evaluation.

    Uses configurable weights for different metric categories:
    - Performance (40% default): accuracy, f1, r2, etc.
    - Robustness (20% default): stability metrics
    - Latency (20% default): inference speed
    - Cost (20% default): computational/token cost
    """

    def __init__(
        self,
        config: ScoringConfig | None = None,
        task_type: TaskType = TaskType.CLASSIFICATION,
    ):
        """
        Initialize the scorer.

        Args:
            config: Scoring configuration
            task_type: Task type for metric category mapping
        """
        self.config = config or ScoringConfig()
        self.task_type = task_type
        self._metric_categories = (
            CLASSIFICATION_METRIC_CATEGORIES if task_type == TaskType.CLASSIFICATION else REGRESSION_METRIC_CATEGORIES
        )

    def score_single(
        self,
        model_name: str,
        metrics: dict[str, float],
        latency_ms: float | None = None,
        cost: float | None = None,
    ) -> ScoringResult:
        """
        Compute global score for a single model.

        Args:
            model_name: Name of the model
            metrics: Dict of metric name to value
            latency_ms: Inference latency in milliseconds
            cost: Cost per inference (e.g., token cost)

        Returns:
            ScoringResult with global score and breakdown
        """
        # Normalize metrics
        normalized = self._normalize_metrics(metrics)

        # Add latency and cost if provided
        if latency_ms is not None:
            # Lower latency is better, normalize inversely
            # Assume 1000ms as max acceptable latency
            normalized["latency"] = max(0, 1 - latency_ms / 1000)

        if cost is not None:
            # Lower cost is better, normalize inversely
            # Assume $1 as max acceptable cost
            normalized["cost"] = max(0, 1 - cost)

        # Compute category scores
        category_scores = self._compute_category_scores(normalized)

        # Compute global score
        global_score = self._compute_global_score(category_scores)

        return ScoringResult(
            model_name=model_name,
            global_score=global_score,
            category_scores=category_scores,
            normalized_metrics=normalized,
            raw_metrics=metrics,
        )

    def score_multiple(
        self,
        results: list[dict[str, Any]],
    ) -> list[ScoringResult]:
        """
        Score multiple models and assign ranks.

        Args:
            results: List of result dicts with metrics, latency, cost

        Returns:
            List of ScoringResults with ranks assigned
        """
        scoring_results = []

        for result in results:
            model_name = result.get("model_name", "Unknown")
            metrics = result.get("metrics", {})
            latency_ms = result.get("inference_latency_ms")
            cost = result.get("cost")

            # Skip if no metrics (failed models)
            if not metrics:
                scoring_results.append(
                    ScoringResult(
                        model_name=model_name,
                        global_score=0.0,
                        is_valid=False,
                        constraint_violations=["No metrics available"],
                        raw_metrics={},
                    )
                )
                continue

            score_result = self.score_single(
                model_name=model_name,
                metrics=metrics,
                latency_ms=latency_ms,
                cost=cost,
            )
            scoring_results.append(score_result)

        # Assign ranks (higher score = better = lower rank number)
        valid_results = [r for r in scoring_results if r.is_valid and r.global_score > 0]
        valid_results.sort(key=lambda r: r.global_score, reverse=True)

        for rank, result in enumerate(valid_results, start=1):
            result.rank = rank

        logger.info(
            "models_scored",
            total_models=len(scoring_results),
            valid_models=len(valid_results),
        )

        return scoring_results

    def _normalize_metrics(self, metrics: dict[str, float]) -> dict[str, float]:
        """
        Normalize metrics to [0, 1] range.

        Higher is better after normalization.

        Args:
            metrics: Raw metric values

        Returns:
            Normalized metric values
        """
        if not self.config.normalize_metrics:
            return metrics.copy()

        normalized = {}

        for name, value in metrics.items():
            if value is None:
                continue

            # Handle metrics where lower is better
            if name not in HIGHER_IS_BETTER:
                # Invert so that higher normalized value = better
                # Use different strategies based on metric type
                if name in {"rmse", "mse", "mae", "mape", "median_ae", "max_error_value"}:
                    # For error metrics, assume max of 1.0 for normalization
                    # In practice, you'd want to use actual min/max from data
                    normalized[name] = max(0, 1 - min(value, 1.0))
                elif name == "log_loss_value":
                    # Log loss: lower is better, typical range 0-2
                    normalized[name] = max(0, 1 - value / 2)
                else:
                    normalized[name] = value
            else:
                # For higher-is-better metrics, already in [0, 1] range
                # Clamp to be safe
                normalized[name] = max(0, min(1, value))

        return normalized

    def _compute_category_scores(
        self,
        normalized: dict[str, float],
    ) -> dict[str, float]:
        """
        Compute scores for each category.

        Args:
            normalized: Normalized metric values

        Returns:
            Dict of category to aggregated score
        """
        category_sums: dict[str, float] = {}
        category_counts: dict[str, int] = {}

        for metric, value in normalized.items():
            category = self._metric_categories.get(metric)
            if category is None:
                # Check if it's a special metric (latency, cost)
                if metric in {"latency", "cost"}:
                    category = metric
                else:
                    continue

            if category not in category_sums:
                category_sums[category] = 0.0
                category_counts[category] = 0

            category_sums[category] += value
            category_counts[category] += 1

        # Average per category
        category_scores = {}
        for category in category_sums:
            if category_counts[category] > 0:
                category_scores[category] = category_sums[category] / category_counts[category]

        return category_scores

    def _compute_global_score(self, category_scores: dict[str, float]) -> float:
        """
        Compute weighted global score from category scores.

        Args:
            category_scores: Score per category

        Returns:
            Global weighted score
        """
        # If primary metric is set, use it directly
        if self.config.primary_metric and self.config.primary_metric in category_scores:
            return category_scores[self.config.primary_metric]

        total_score = 0.0
        total_weight = 0.0

        for category, weight in self.config.weights.items():
            if category in category_scores:
                total_score += category_scores[category] * weight
                total_weight += weight

        # Normalize by actual weights used (in case some categories missing)
        if total_weight > 0:
            return total_score / total_weight
        return 0.0

    def get_recommendation(
        self,
        scoring_results: list[ScoringResult],
    ) -> str:
        """
        Generate a plain-language recommendation.

        Args:
            scoring_results: List of scoring results with ranks

        Returns:
            Recommendation string
        """
        valid = [r for r in scoring_results if r.is_valid and r.rank is not None]

        if not valid:
            return "No models passed evaluation. Please review constraints and data quality."

        best = min(valid, key=lambda r: r.rank or float("inf"))

        # Build recommendation
        recommendation = f"Based on weighted evaluation, **{best.model_name}** is recommended "
        recommendation += f"with a global score of {best.global_score:.3f}. "

        # Add category breakdown
        if best.category_scores:
            top_category = max(best.category_scores.items(), key=lambda x: x[1])
            recommendation += f"It excels in {top_category[0]} ({top_category[1]:.3f}). "

        # Mention runner-up if available
        if len(valid) > 1:
            second = sorted(valid, key=lambda r: r.rank or float("inf"))[1]
            recommendation += f"Runner-up: {second.model_name} (score: {second.global_score:.3f})."

        return recommendation
