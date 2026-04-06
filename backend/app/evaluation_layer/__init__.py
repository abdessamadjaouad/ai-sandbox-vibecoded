# backend/app/evaluation_layer/__init__.py
"""
Evaluation Layer — metrics computation, scoring, and report generation.

This layer handles:
- Metric computation for classification, regression, LLM, and agent evaluation
- Weighted global scoring with configurable weights
- Constraint checking (latency, cost thresholds)
- Report generation in Markdown/PDF formats
"""

from backend.app.evaluation_layer.metrics import (
    ClassificationMetrics,
    RegressionMetrics,
    MetricsCalculator,
)
from backend.app.evaluation_layer.scoring import (
    WeightedScorer,
    ScoringConfig,
    ConstraintChecker,
)
from backend.app.evaluation_layer.reports import (
    ReportGenerator,
    ReportConfig,
)

__all__ = [
    "ClassificationMetrics",
    "RegressionMetrics",
    "MetricsCalculator",
    "WeightedScorer",
    "ScoringConfig",
    "ConstraintChecker",
    "ReportGenerator",
    "ReportConfig",
]
