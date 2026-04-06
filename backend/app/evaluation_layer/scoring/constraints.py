# backend/app/evaluation_layer/scoring/constraints.py
"""
Constraint checking for model evaluation.

Validates that models meet required thresholds for latency, cost, and metrics.
"""

from typing import Any

from pydantic import BaseModel, Field

import structlog

logger = structlog.get_logger(__name__)


class ConstraintConfig(BaseModel):
    """Configuration for constraint checking."""

    max_latency_ms: float | None = Field(
        None,
        description="Maximum allowed inference latency in milliseconds",
    )
    max_cost_per_request: float | None = Field(
        None,
        description="Maximum allowed cost per request in dollars",
    )
    min_accuracy: float | None = Field(
        None,
        description="Minimum required accuracy (classification)",
    )
    min_f1: float | None = Field(
        None,
        description="Minimum required F1 score (classification)",
    )
    min_r2: float | None = Field(
        None,
        description="Minimum required R² score (regression)",
    )
    max_rmse: float | None = Field(
        None,
        description="Maximum allowed RMSE (regression)",
    )
    custom_constraints: dict[str, dict[str, float]] | None = Field(
        None,
        description="Custom constraints: {metric_name: {'min': value} or {'max': value}}",
    )


class ConstraintResult(BaseModel):
    """Result of constraint checking."""

    model_name: str = Field(..., description="Model name")
    passed: bool = Field(..., description="Whether all constraints passed")
    violations: list[str] = Field(
        default_factory=list,
        description="List of constraint violations",
    )
    checked_constraints: dict[str, bool] = Field(
        default_factory=dict,
        description="Each constraint and whether it passed",
    )


class ConstraintChecker:
    """
    Check if models meet required constraints.

    Validates models against latency, cost, and metric thresholds.
    Models that violate constraints can be penalized or excluded.
    """

    def __init__(self, config: ConstraintConfig | None = None):
        """
        Initialize the constraint checker.

        Args:
            config: Constraint configuration
        """
        self.config = config or ConstraintConfig()

    def check(
        self,
        model_name: str,
        metrics: dict[str, float],
        latency_ms: float | None = None,
        cost: float | None = None,
    ) -> ConstraintResult:
        """
        Check constraints for a single model.

        Args:
            model_name: Name of the model
            metrics: Dict of metric name to value
            latency_ms: Inference latency in milliseconds
            cost: Cost per inference

        Returns:
            ConstraintResult with pass/fail and violations
        """
        violations = []
        checked = {}

        # Check latency constraint
        if self.config.max_latency_ms is not None and latency_ms is not None:
            passed = latency_ms <= self.config.max_latency_ms
            checked["latency"] = passed
            if not passed:
                violations.append(f"Latency {latency_ms:.1f}ms exceeds max {self.config.max_latency_ms:.1f}ms")

        # Check cost constraint
        if self.config.max_cost_per_request is not None and cost is not None:
            passed = cost <= self.config.max_cost_per_request
            checked["cost"] = passed
            if not passed:
                violations.append(f"Cost ${cost:.4f} exceeds max ${self.config.max_cost_per_request:.4f}")

        # Check accuracy constraint
        if self.config.min_accuracy is not None and "accuracy" in metrics:
            passed = metrics["accuracy"] >= self.config.min_accuracy
            checked["min_accuracy"] = passed
            if not passed:
                violations.append(f"Accuracy {metrics['accuracy']:.3f} below min {self.config.min_accuracy:.3f}")

        # Check F1 constraint
        if self.config.min_f1 is not None and "f1" in metrics:
            passed = metrics["f1"] >= self.config.min_f1
            checked["min_f1"] = passed
            if not passed:
                violations.append(f"F1 {metrics['f1']:.3f} below min {self.config.min_f1:.3f}")

        # Check R² constraint
        if self.config.min_r2 is not None and "r2" in metrics:
            passed = metrics["r2"] >= self.config.min_r2
            checked["min_r2"] = passed
            if not passed:
                violations.append(f"R² {metrics['r2']:.3f} below min {self.config.min_r2:.3f}")

        # Check RMSE constraint
        if self.config.max_rmse is not None and "rmse" in metrics:
            passed = metrics["rmse"] <= self.config.max_rmse
            checked["max_rmse"] = passed
            if not passed:
                violations.append(f"RMSE {metrics['rmse']:.3f} exceeds max {self.config.max_rmse:.3f}")

        # Check custom constraints
        if self.config.custom_constraints:
            for metric_name, bounds in self.config.custom_constraints.items():
                if metric_name not in metrics:
                    continue

                value = metrics[metric_name]

                if "min" in bounds:
                    passed = value >= bounds["min"]
                    checked[f"min_{metric_name}"] = passed
                    if not passed:
                        violations.append(f"{metric_name} {value:.3f} below min {bounds['min']:.3f}")

                if "max" in bounds:
                    passed = value <= bounds["max"]
                    checked[f"max_{metric_name}"] = passed
                    if not passed:
                        violations.append(f"{metric_name} {value:.3f} exceeds max {bounds['max']:.3f}")

        all_passed = len(violations) == 0

        if violations:
            logger.info(
                "constraint_violations",
                model_name=model_name,
                violations=violations,
            )

        return ConstraintResult(
            model_name=model_name,
            passed=all_passed,
            violations=violations,
            checked_constraints=checked,
        )

    def check_multiple(
        self,
        results: list[dict[str, Any]],
    ) -> list[ConstraintResult]:
        """
        Check constraints for multiple models.

        Args:
            results: List of result dicts with metrics, latency, cost

        Returns:
            List of ConstraintResults
        """
        constraint_results = []

        for result in results:
            model_name = result.get("model_name", "Unknown")
            metrics = result.get("metrics", {})
            latency_ms = result.get("inference_latency_ms")
            cost = result.get("cost")

            constraint_result = self.check(
                model_name=model_name,
                metrics=metrics,
                latency_ms=latency_ms,
                cost=cost,
            )
            constraint_results.append(constraint_result)

        passed_count = sum(1 for r in constraint_results if r.passed)
        logger.info(
            "constraints_checked",
            total_models=len(constraint_results),
            passed_models=passed_count,
        )

        return constraint_results

    def filter_passing(
        self,
        results: list[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """
        Filter results into passing and failing based on constraints.

        Args:
            results: List of result dicts

        Returns:
            Tuple of (passing_results, failing_results)
        """
        constraint_results = self.check_multiple(results)

        passing = []
        failing = []

        for result, constraint in zip(results, constraint_results):
            if constraint.passed:
                passing.append(result)
            else:
                # Add violations to result
                result_copy = dict(result)
                result_copy["constraint_violations"] = constraint.violations
                failing.append(result_copy)

        return passing, failing
