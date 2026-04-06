# tests/unit/test_evaluation_layer/test_scoring.py
"""Tests for evaluation scoring module."""

import pytest

from backend.app.evaluation_layer.scoring import (
    WeightedScorer,
    ScoringConfig,
    ConstraintChecker,
    ConstraintConfig,
)
from backend.app.models.experiment import TaskType


class TestWeightedScorer:
    """Tests for weighted global scoring."""

    def test_score_single_classification_model(self):
        """Scores a single classification model with expected bounds."""
        scorer = WeightedScorer(task_type=TaskType.CLASSIFICATION)

        result = scorer.score_single(
            model_name="RandomForest",
            metrics={"accuracy": 0.9, "f1": 0.88, "precision": 0.87, "recall": 0.89},
            latency_ms=50,
            cost=0.02,
        )

        assert result.model_name == "RandomForest"
        assert 0 <= result.global_score <= 1
        assert "performance" in result.category_scores

    def test_score_multiple_assigns_ranks(self):
        """Assigns rank=1 to best model by score."""
        scorer = WeightedScorer(task_type=TaskType.CLASSIFICATION)

        results = [
            {
                "model_name": "Model A",
                "metrics": {"accuracy": 0.92, "f1": 0.90},
                "inference_latency_ms": 40,
            },
            {
                "model_name": "Model B",
                "metrics": {"accuracy": 0.80, "f1": 0.78},
                "inference_latency_ms": 40,
            },
        ]

        scored = scorer.score_multiple(results)

        valid = [r for r in scored if r.rank is not None]
        assert len(valid) == 2
        best = min(valid, key=lambda x: x.rank)
        assert best.model_name == "Model A"

    def test_invalid_weights_raise_error(self):
        """Raises when weights do not sum to 1."""
        with pytest.raises(ValueError):
            ScoringConfig(weights={"performance": 0.5, "robustness": 0.5, "latency": 0.5, "cost": 0.5})

    def test_get_recommendation_for_valid_models(self):
        """Returns recommendation text with best model name."""
        scorer = WeightedScorer(task_type=TaskType.CLASSIFICATION)

        scored = scorer.score_multiple(
            [
                {"model_name": "Model A", "metrics": {"accuracy": 0.95, "f1": 0.94}},
                {"model_name": "Model B", "metrics": {"accuracy": 0.80, "f1": 0.79}},
            ]
        )
        recommendation = scorer.get_recommendation(scored)

        assert "Model A" in recommendation


class TestConstraintChecker:
    """Tests for constraint checking logic."""

    def test_passes_when_all_constraints_met(self):
        """Passes model when all configured constraints are satisfied."""
        checker = ConstraintChecker(
            ConstraintConfig(
                max_latency_ms=100,
                max_cost_per_request=0.1,
                min_accuracy=0.8,
                min_f1=0.75,
            )
        )

        result = checker.check(
            model_name="Model A",
            metrics={"accuracy": 0.9, "f1": 0.85},
            latency_ms=50,
            cost=0.05,
        )

        assert result.passed is True
        assert result.violations == []

    def test_fails_when_constraints_violated(self):
        """Captures violations when constraints are exceeded."""
        checker = ConstraintChecker(
            ConstraintConfig(
                max_latency_ms=20,
                min_accuracy=0.95,
            )
        )

        result = checker.check(
            model_name="Model B",
            metrics={"accuracy": 0.80, "f1": 0.78},
            latency_ms=40,
            cost=0.01,
        )

        assert result.passed is False
        assert len(result.violations) >= 1

    def test_filter_passing_splits_results(self):
        """Splits input models into passing and failing lists."""
        checker = ConstraintChecker(ConstraintConfig(min_accuracy=0.9))

        passing, failing = checker.filter_passing(
            [
                {"model_name": "A", "metrics": {"accuracy": 0.95}},
                {"model_name": "B", "metrics": {"accuracy": 0.70}},
            ]
        )

        assert len(passing) == 1
        assert len(failing) == 1
        assert passing[0]["model_name"] == "A"
        assert failing[0]["model_name"] == "B"
