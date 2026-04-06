# backend/app/evaluation_layer/reports/generator.py
"""
Report generation for experiment results.

Generates Markdown reports with visualizations and recommendations.
"""

from datetime import datetime
from typing import Any
import uuid

from pydantic import BaseModel, Field

from backend.app.models.experiment import TaskType, ExperimentStatus
from backend.app.evaluation_layer.scoring.scorer import ScoringResult

import structlog

logger = structlog.get_logger(__name__)


class ReportConfig(BaseModel):
    """Configuration for report generation."""

    include_per_model_details: bool = Field(
        True,
        description="Include detailed metrics for each model",
    )
    include_confusion_matrix: bool = Field(
        True,
        description="Include confusion matrix (classification only)",
    )
    include_recommendations: bool = Field(
        True,
        description="Include plain-language recommendations",
    )
    include_constraints_summary: bool = Field(
        True,
        description="Include constraint violations summary",
    )
    max_models_in_table: int = Field(
        20,
        description="Maximum models to show in comparison table",
    )
    decimal_precision: int = Field(
        4,
        description="Decimal places for metric values",
    )


class ExperimentReport(BaseModel):
    """Generated experiment report."""

    experiment_id: uuid.UUID = Field(..., description="Experiment ID")
    experiment_name: str = Field(..., description="Experiment name")
    generated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Report generation timestamp",
    )
    markdown_content: str = Field(..., description="Full Markdown report")
    summary: str = Field(..., description="Plain-language summary")
    recommendation: str = Field(..., description="Best model recommendation")
    best_model: str | None = Field(None, description="Name of best model")
    best_score: float | None = Field(None, description="Score of best model")


class ReportGenerator:
    """
    Generate evaluation reports in Markdown format.

    Creates comprehensive reports with:
    - Executive summary with recommendation
    - Model comparison table
    - Per-model detailed metrics
    - Constraint violations
    - Configuration used
    """

    def __init__(self, config: ReportConfig | None = None):
        """
        Initialize the report generator.

        Args:
            config: Report configuration
        """
        self.config = config or ReportConfig()

    def generate(
        self,
        experiment_id: uuid.UUID,
        experiment_name: str,
        task_type: TaskType,
        status: ExperimentStatus,
        scoring_results: list[ScoringResult],
        dataset_info: dict[str, Any] | None = None,
        duration_seconds: float | None = None,
        constraints_config: dict[str, Any] | None = None,
    ) -> ExperimentReport:
        """
        Generate a full experiment report.

        Args:
            experiment_id: Experiment UUID
            experiment_name: Name of the experiment
            task_type: Classification or regression
            status: Experiment status
            scoring_results: List of scoring results
            dataset_info: Optional dataset metadata
            duration_seconds: Experiment duration
            constraints_config: Constraint configuration used

        Returns:
            ExperimentReport with Markdown content
        """
        prec = self.config.decimal_precision

        # Find best model
        valid_results = [r for r in scoring_results if r.is_valid and r.rank is not None]
        best = min(valid_results, key=lambda r: r.rank or float("inf")) if valid_results else None

        # Generate sections
        sections = []

        # Header
        sections.append(self._generate_header(experiment_name, experiment_id))

        # Executive Summary
        summary = self._generate_summary(
            status=status,
            task_type=task_type,
            scoring_results=scoring_results,
            best=best,
            duration_seconds=duration_seconds,
        )
        sections.append(summary)

        # Recommendation
        recommendation = self._generate_recommendation(best, scoring_results)
        if self.config.include_recommendations:
            sections.append(f"## Recommendation\n\n{recommendation}\n")

        # Model Comparison Table
        sections.append(self._generate_comparison_table(scoring_results, task_type, prec))

        # Per-Model Details
        if self.config.include_per_model_details:
            sections.append(self._generate_model_details(scoring_results, task_type, prec))

        # Constraint Violations
        if self.config.include_constraints_summary:
            violations_section = self._generate_violations_summary(scoring_results)
            if violations_section:
                sections.append(violations_section)

        # Dataset Info
        if dataset_info:
            sections.append(self._generate_dataset_info(dataset_info))

        # Configuration
        if constraints_config:
            sections.append(self._generate_config_section(constraints_config))

        # Footer
        sections.append(self._generate_footer())

        markdown = "\n\n".join(sections)

        logger.info(
            "report_generated",
            experiment_id=str(experiment_id),
            total_models=len(scoring_results),
            best_model=best.model_name if best else None,
        )

        return ExperimentReport(
            experiment_id=experiment_id,
            experiment_name=experiment_name,
            markdown_content=markdown,
            summary=summary,
            recommendation=recommendation,
            best_model=best.model_name if best else None,
            best_score=best.global_score if best else None,
        )

    def _generate_header(self, name: str, exp_id: uuid.UUID) -> str:
        """Generate report header."""
        return f"""# Experiment Report: {name}

**Experiment ID:** `{exp_id}`  
**Generated:** {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")} UTC"""

    def _generate_summary(
        self,
        status: ExperimentStatus,
        task_type: TaskType,
        scoring_results: list[ScoringResult],
        best: ScoringResult | None,
        duration_seconds: float | None,
    ) -> str:
        """Generate executive summary."""
        total = len(scoring_results)
        valid = sum(1 for r in scoring_results if r.is_valid)
        failed = total - valid

        lines = ["## Executive Summary", ""]

        # Status
        status_emoji = "✅" if status == ExperimentStatus.COMPLETED else "❌"
        lines.append(f"**Status:** {status_emoji} {status.value.title()}")
        lines.append(f"**Task Type:** {task_type.value.title()}")
        lines.append(f"**Models Evaluated:** {total} ({valid} passed, {failed} failed constraints)")

        if duration_seconds:
            if duration_seconds < 60:
                lines.append(f"**Duration:** {duration_seconds:.1f} seconds")
            else:
                minutes = duration_seconds / 60
                lines.append(f"**Duration:** {minutes:.1f} minutes")

        if best:
            lines.append("")
            lines.append(f"**Best Model:** {best.model_name}")
            lines.append(f"**Best Score:** {best.global_score:.4f}")

        return "\n".join(lines)

    def _generate_recommendation(
        self,
        best: ScoringResult | None,
        scoring_results: list[ScoringResult],
    ) -> str:
        """Generate plain-language recommendation."""
        if not best:
            return (
                "No models passed evaluation. Please review the constraint configuration "
                "and ensure your data is suitable for the selected task type."
            )

        rec = f"Based on weighted evaluation across performance, robustness, latency, and cost, "
        rec += f"**{best.model_name}** is recommended with a global score of **{best.global_score:.4f}**."

        # Category breakdown
        if best.category_scores:
            rec += "\n\nCategory scores:\n"
            for cat, score in sorted(best.category_scores.items(), key=lambda x: -x[1]):
                rec += f"- {cat.title()}: {score:.4f}\n"

        # Runner-up
        valid = [r for r in scoring_results if r.is_valid and r.rank is not None and r.rank > 1]
        if valid:
            runner_up = min(valid, key=lambda r: r.rank or float("inf"))
            rec += f"\n**Runner-up:** {runner_up.model_name} (score: {runner_up.global_score:.4f})"

        return rec

    def _generate_comparison_table(
        self,
        scoring_results: list[ScoringResult],
        task_type: TaskType,
        prec: int,
    ) -> str:
        """Generate model comparison table."""
        lines = ["## Model Comparison", ""]

        # Sort by rank (best first)
        sorted_results = sorted(
            scoring_results,
            key=lambda r: (r.rank or float("inf"), -r.global_score),
        )

        # Limit to max models
        sorted_results = sorted_results[: self.config.max_models_in_table]

        # Determine metrics to show based on task type
        if task_type == TaskType.CLASSIFICATION:
            metric_cols = ["accuracy", "f1", "precision", "recall", "auc_roc"]
        else:
            metric_cols = ["rmse", "mae", "r2", "mape"]

        # Build header
        header = "| Rank | Model | Global Score |"
        divider = "|:----:|:------|:------------:|"
        for col in metric_cols:
            header += f" {col.upper()} |"
            divider += ":------:|"
        header += " Status |"
        divider += ":------:|"

        lines.append(header)
        lines.append(divider)

        # Build rows
        for r in sorted_results:
            rank_str = str(r.rank) if r.rank else "-"
            status = "✅" if r.is_valid else "❌"
            row = f"| {rank_str} | {r.model_name} | {r.global_score:.{prec}f} |"

            for col in metric_cols:
                val = r.raw_metrics.get(col)
                if val is not None:
                    row += f" {val:.{prec}f} |"
                else:
                    row += " - |"

            row += f" {status} |"
            lines.append(row)

        return "\n".join(lines)

    def _generate_model_details(
        self,
        scoring_results: list[ScoringResult],
        task_type: TaskType,
        prec: int,
    ) -> str:
        """Generate per-model detailed metrics."""
        lines = ["## Model Details", ""]

        # Only show top models in detail
        valid_results = sorted(
            [r for r in scoring_results if r.is_valid],
            key=lambda r: r.rank or float("inf"),
        )[:5]

        for r in valid_results:
            lines.append(f"### {r.model_name}")
            lines.append("")
            lines.append(f"**Rank:** #{r.rank} | **Global Score:** {r.global_score:.{prec}f}")
            lines.append("")

            # Category scores
            if r.category_scores:
                lines.append("**Category Breakdown:**")
                for cat, score in r.category_scores.items():
                    lines.append(f"- {cat.title()}: {score:.{prec}f}")
                lines.append("")

            # All metrics
            if r.raw_metrics:
                lines.append("**All Metrics:**")
                lines.append("")
                lines.append("| Metric | Value |")
                lines.append("|:-------|------:|")
                for metric, value in sorted(r.raw_metrics.items()):
                    if isinstance(value, (int, float)):
                        lines.append(f"| {metric} | {value:.{prec}f} |")
                lines.append("")

        return "\n".join(lines)

    def _generate_violations_summary(
        self,
        scoring_results: list[ScoringResult],
    ) -> str | None:
        """Generate constraint violations summary."""
        failed = [r for r in scoring_results if not r.is_valid]

        if not failed:
            return None

        lines = ["## Constraint Violations", ""]
        lines.append(f"**{len(failed)} model(s) failed constraints:**")
        lines.append("")

        for r in failed:
            lines.append(f"### {r.model_name}")
            for v in r.constraint_violations:
                lines.append(f"- {v}")
            lines.append("")

        return "\n".join(lines)

    def _generate_dataset_info(self, info: dict[str, Any]) -> str:
        """Generate dataset information section."""
        lines = ["## Dataset Information", ""]

        for key, value in info.items():
            lines.append(f"- **{key.replace('_', ' ').title()}:** {value}")

        return "\n".join(lines)

    def _generate_config_section(self, config: dict[str, Any]) -> str:
        """Generate configuration section."""
        lines = ["## Configuration", ""]
        lines.append("```json")

        import json

        lines.append(json.dumps(config, indent=2, default=str))
        lines.append("```")

        return "\n".join(lines)

    def _generate_footer(self) -> str:
        """Generate report footer."""
        return """---

*Generated by AI Sandbox Evaluation Layer*"""

    def generate_comparison_only(
        self,
        scoring_results: list[ScoringResult],
        task_type: TaskType,
    ) -> str:
        """
        Generate a quick comparison table only.

        Args:
            scoring_results: Scoring results
            task_type: Task type

        Returns:
            Markdown table string
        """
        return self._generate_comparison_table(scoring_results, task_type, self.config.decimal_precision)
