# tests/unit/test_evaluation_layer/test_reports.py
"""Tests for evaluation report generation."""

import uuid

from backend.app.evaluation_layer.reports import ReportGenerator
from backend.app.evaluation_layer.scoring import ScoringResult
from backend.app.models.experiment import TaskType, ExperimentStatus


def _sample_scoring_results() -> list[ScoringResult]:
    return [
        ScoringResult(
            model_name="Model A",
            global_score=0.91,
            rank=1,
            category_scores={"performance": 0.93, "robustness": 0.88},
            raw_metrics={"accuracy": 0.92, "f1": 0.90},
            is_valid=True,
        ),
        ScoringResult(
            model_name="Model B",
            global_score=0.84,
            rank=2,
            category_scores={"performance": 0.86, "robustness": 0.80},
            raw_metrics={"accuracy": 0.85, "f1": 0.83},
            is_valid=True,
        ),
    ]


def test_generate_report_includes_key_sections():
    """Generates markdown report containing key section headers."""
    generator = ReportGenerator()

    report = generator.generate(
        experiment_id=uuid.uuid4(),
        experiment_name="Eval Test",
        task_type=TaskType.CLASSIFICATION,
        status=ExperimentStatus.COMPLETED,
        scoring_results=_sample_scoring_results(),
        duration_seconds=12.5,
    )

    assert "# Experiment Report: Eval Test" in report.markdown_content
    assert "## Executive Summary" in report.markdown_content
    assert "## Recommendation" in report.markdown_content
    assert "## Model Comparison" in report.markdown_content
    assert report.best_model == "Model A"


def test_generate_report_handles_no_valid_models():
    """Returns fallback recommendation when no valid models exist."""
    generator = ReportGenerator()
    failed_only = [
        ScoringResult(
            model_name="BadModel",
            global_score=0.0,
            is_valid=False,
            constraint_violations=["No metrics available"],
        )
    ]

    report = generator.generate(
        experiment_id=uuid.uuid4(),
        experiment_name="Failed Eval",
        task_type=TaskType.CLASSIFICATION,
        status=ExperimentStatus.FAILED,
        scoring_results=failed_only,
    )

    assert "No models passed evaluation" in report.recommendation
    assert report.best_model is None


def test_generate_comparison_only_contains_table():
    """Generates comparison-only markdown table section."""
    generator = ReportGenerator()
    content = generator.generate_comparison_only(
        scoring_results=_sample_scoring_results(),
        task_type=TaskType.CLASSIFICATION,
    )

    assert "## Model Comparison" in content
    assert "| Rank | Model | Global Score |" in content
