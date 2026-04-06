# tests/unit/test_experiment_layer/test_catalogue.py
"""Tests for model catalogue."""

import pytest

from backend.app.experiment_layer.orchestrator.catalogue import (
    ModelCatalogue,
    ModelDefinition,
    get_catalogue,
)
from backend.app.models.experiment import ModelFamily, TaskType


class TestModelDefinition:
    """Tests for ModelDefinition class."""

    def test_definition_instantiate_creates_model(self):
        """instantiate creates a model instance with correct parameters."""
        from sklearn.ensemble import RandomForestClassifier

        definition = ModelDefinition(
            name="Random Forest",
            family=ModelFamily.SKLEARN,
            class_ref=RandomForestClassifier,
            task_types=[TaskType.CLASSIFICATION],
            default_hyperparameters={"n_estimators": 50},
            description="Test model",
        )

        model = definition.instantiate(random_seed=123)

        assert isinstance(model, RandomForestClassifier)
        assert model.n_estimators == 50
        assert model.random_state == 123

    def test_definition_instantiate_with_overrides(self):
        """instantiate applies hyperparameter overrides."""
        from sklearn.ensemble import RandomForestClassifier

        definition = ModelDefinition(
            name="Random Forest",
            family=ModelFamily.SKLEARN,
            class_ref=RandomForestClassifier,
            task_types=[TaskType.CLASSIFICATION],
            default_hyperparameters={"n_estimators": 50, "max_depth": 10},
        )

        model = definition.instantiate(
            hyperparameters={"n_estimators": 200},
            random_seed=42,
        )

        assert model.n_estimators == 200
        assert model.max_depth == 10

    def test_definition_to_dict(self):
        """to_dict returns correct dictionary representation."""
        from sklearn.linear_model import LogisticRegression

        definition = ModelDefinition(
            name="Logistic Regression",
            family=ModelFamily.SKLEARN,
            class_ref=LogisticRegression,
            task_types=[TaskType.CLASSIFICATION],
            default_hyperparameters={"max_iter": 1000},
            description="Linear classifier",
        )

        result = definition.to_dict()

        assert result["name"] == "Logistic Regression"
        assert result["family"] == "sklearn"
        assert "sklearn.linear_model" in result["class_name"]
        assert result["task_types"] == ["classification"]
        assert result["default_hyperparameters"] == {"max_iter": 1000}


class TestModelCatalogue:
    """Tests for ModelCatalogue class."""

    def test_catalogue_registers_default_models(self):
        """Catalogue is initialized with default models."""
        catalogue = ModelCatalogue()
        all_models = catalogue.list_all()

        # Should have multiple default models
        assert len(all_models) >= 10

        # Check for expected models
        names = [m.name for m in all_models]
        assert "Random Forest Classifier" in names
        assert "XGBoost Classifier" in names
        assert "LightGBM Classifier" in names
        assert "Logistic Regression" in names

    def test_catalogue_get_by_name(self):
        """get retrieves model by name (case-insensitive)."""
        catalogue = ModelCatalogue()

        # Exact name
        model = catalogue.get("Random Forest Classifier")
        assert model is not None
        assert model.name == "Random Forest Classifier"

        # Case-insensitive with underscores
        model = catalogue.get("random_forest_classifier")
        assert model is not None

        # Non-existent
        model = catalogue.get("NonExistent Model")
        assert model is None

    def test_catalogue_list_by_task_type(self):
        """list_by_task_type filters correctly."""
        catalogue = ModelCatalogue()

        classifiers = catalogue.list_by_task_type(TaskType.CLASSIFICATION)
        regressors = catalogue.list_by_task_type(TaskType.REGRESSION)

        assert len(classifiers) > 0
        assert len(regressors) > 0

        # All classifiers support classification
        for model in classifiers:
            assert TaskType.CLASSIFICATION in model.task_types

        # All regressors support regression
        for model in regressors:
            assert TaskType.REGRESSION in model.task_types

    def test_catalogue_list_by_family(self):
        """list_by_family filters correctly."""
        catalogue = ModelCatalogue()

        sklearn_models = catalogue.list_by_family(ModelFamily.SKLEARN)
        xgboost_models = catalogue.list_by_family(ModelFamily.XGBOOST)

        assert len(sklearn_models) > 0
        assert len(xgboost_models) > 0

        for model in sklearn_models:
            assert model.family == ModelFamily.SKLEARN

    def test_catalogue_get_default_models_for_task(self):
        """get_default_models_for_task returns curated list."""
        catalogue = ModelCatalogue()

        # Classification defaults
        defaults = catalogue.get_default_models_for_task(TaskType.CLASSIFICATION, max_models=3)

        assert len(defaults) == 3
        assert all("name" in m for m in defaults)
        assert all("family" in m for m in defaults)
        assert all("hyperparameters" in m for m in defaults)

        # Regression defaults
        defaults = catalogue.get_default_models_for_task(TaskType.REGRESSION)
        assert len(defaults) > 0

    def test_catalogue_instantiate_model(self):
        """instantiate_model creates model by name."""
        catalogue = ModelCatalogue()

        model = catalogue.instantiate_model(
            "Random Forest Classifier",
            hyperparameters={"n_estimators": 10},
            random_seed=42,
        )

        from sklearn.ensemble import RandomForestClassifier

        assert isinstance(model, RandomForestClassifier)
        assert model.n_estimators == 10

    def test_catalogue_instantiate_model_not_found_raises(self):
        """instantiate_model raises ValueError for unknown model."""
        catalogue = ModelCatalogue()

        with pytest.raises(ValueError, match="not found"):
            catalogue.instantiate_model("NonExistent Model")

    def test_catalogue_register_custom_model(self):
        """register adds custom model to catalogue."""
        from sklearn.tree import DecisionTreeClassifier

        catalogue = ModelCatalogue()
        initial_count = len(catalogue.list_all())

        # Register custom model
        catalogue.register(
            ModelDefinition(
                name="Custom Tree",
                family=ModelFamily.CUSTOM,
                class_ref=DecisionTreeClassifier,
                task_types=[TaskType.CLASSIFICATION],
                default_hyperparameters={"max_depth": 5},
            )
        )

        assert len(catalogue.list_all()) == initial_count + 1

        model = catalogue.get("Custom Tree")
        assert model is not None


class TestGetCatalogue:
    """Tests for get_catalogue singleton function."""

    def test_get_catalogue_returns_singleton(self):
        """get_catalogue returns the same instance."""
        cat1 = get_catalogue()
        cat2 = get_catalogue()

        assert cat1 is cat2

    def test_get_catalogue_is_populated(self):
        """get_catalogue returns populated catalogue."""
        catalogue = get_catalogue()

        assert len(catalogue.list_all()) >= 10
