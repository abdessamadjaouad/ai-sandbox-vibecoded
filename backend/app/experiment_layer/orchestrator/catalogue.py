# backend/app/experiment_layer/orchestrator/catalogue.py
"""
Model catalogue — registry of available models for experiments.

Provides model definitions, default hyperparameters, and factory
functions for instantiating models based on configuration.
"""

from typing import Any, Callable

from sklearn.ensemble import (
    RandomForestClassifier,
    RandomForestRegressor,
    GradientBoostingClassifier,
    GradientBoostingRegressor,
    AdaBoostClassifier,
    AdaBoostRegressor,
)
from sklearn.linear_model import (
    LogisticRegression,
    Ridge,
    Lasso,
    ElasticNet,
    SGDClassifier,
    SGDRegressor,
)
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.svm import SVC, SVR
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
from sklearn.naive_bayes import GaussianNB
from xgboost import XGBClassifier, XGBRegressor
from lightgbm import LGBMClassifier, LGBMRegressor

from backend.app.models.experiment import ModelFamily, TaskType


# =============================================================================
# Model Definitions
# =============================================================================


class ModelDefinition:
    """
    Definition of a model available in the catalogue.

    Attributes:
        name: Display name for the model
        family: Model family (sklearn, xgboost, lightgbm, etc.)
        class_ref: Reference to the model class
        task_types: List of supported task types
        default_hyperparameters: Default hyperparameters for the model
        description: Human-readable description
    """

    def __init__(
        self,
        name: str,
        family: ModelFamily,
        class_ref: type,
        task_types: list[TaskType],
        default_hyperparameters: dict[str, Any],
        description: str = "",
    ):
        self.name = name
        self.family = family
        self.class_ref = class_ref
        self.task_types = task_types
        self.default_hyperparameters = default_hyperparameters
        self.description = description

    def instantiate(
        self,
        hyperparameters: dict[str, Any] | None = None,
        random_seed: int = 42,
    ) -> Any:
        """
        Create an instance of the model with given hyperparameters.

        Args:
            hyperparameters: Hyperparameters to override defaults
            random_seed: Random seed for reproducibility

        Returns:
            Instantiated model object
        """
        params = {**self.default_hyperparameters}
        if hyperparameters:
            params.update(hyperparameters)

        # Add random_state if the model supports it
        if "random_state" not in params:
            # Check if model accepts random_state
            import inspect

            sig = inspect.signature(self.class_ref.__init__)
            if "random_state" in sig.parameters:
                params["random_state"] = random_seed

        return self.class_ref(**params)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "family": self.family.value,
            "class_name": f"{self.class_ref.__module__}.{self.class_ref.__name__}",
            "task_types": [t.value for t in self.task_types],
            "default_hyperparameters": self.default_hyperparameters,
            "description": self.description,
        }


# =============================================================================
# Catalogue Registry
# =============================================================================


class ModelCatalogue:
    """
    Registry of available models for experiments.

    Provides methods to list, filter, and instantiate models
    based on task type and other criteria.
    """

    def __init__(self):
        self._models: dict[str, ModelDefinition] = {}
        self._register_default_models()

    def _register_default_models(self) -> None:
        """Register all default models in the catalogue."""
        # Classification models
        self.register(
            ModelDefinition(
                name="Random Forest Classifier",
                family=ModelFamily.SKLEARN,
                class_ref=RandomForestClassifier,
                task_types=[TaskType.CLASSIFICATION],
                default_hyperparameters={
                    "n_estimators": 100,
                    "max_depth": None,
                    "min_samples_split": 2,
                    "min_samples_leaf": 1,
                    "n_jobs": -1,
                },
                description="Ensemble of decision trees using bagging",
            )
        )

        self.register(
            ModelDefinition(
                name="Gradient Boosting Classifier",
                family=ModelFamily.SKLEARN,
                class_ref=GradientBoostingClassifier,
                task_types=[TaskType.CLASSIFICATION],
                default_hyperparameters={
                    "n_estimators": 100,
                    "learning_rate": 0.1,
                    "max_depth": 3,
                },
                description="Sequential ensemble using boosting",
            )
        )

        self.register(
            ModelDefinition(
                name="XGBoost Classifier",
                family=ModelFamily.XGBOOST,
                class_ref=XGBClassifier,
                task_types=[TaskType.CLASSIFICATION],
                default_hyperparameters={
                    "n_estimators": 100,
                    "learning_rate": 0.1,
                    "max_depth": 6,
                    "use_label_encoder": False,
                    "eval_metric": "logloss",
                },
                description="Optimized gradient boosting implementation",
            )
        )

        self.register(
            ModelDefinition(
                name="LightGBM Classifier",
                family=ModelFamily.LIGHTGBM,
                class_ref=LGBMClassifier,
                task_types=[TaskType.CLASSIFICATION],
                default_hyperparameters={
                    "n_estimators": 100,
                    "learning_rate": 0.1,
                    "max_depth": -1,
                    "num_leaves": 31,
                    "verbosity": -1,
                },
                description="Fast gradient boosting with histogram-based learning",
            )
        )

        self.register(
            ModelDefinition(
                name="Logistic Regression",
                family=ModelFamily.SKLEARN,
                class_ref=LogisticRegression,
                task_types=[TaskType.CLASSIFICATION],
                default_hyperparameters={
                    "max_iter": 1000,
                    "solver": "lbfgs",
                },
                description="Linear model for classification",
            )
        )

        self.register(
            ModelDefinition(
                name="Decision Tree Classifier",
                family=ModelFamily.SKLEARN,
                class_ref=DecisionTreeClassifier,
                task_types=[TaskType.CLASSIFICATION],
                default_hyperparameters={
                    "max_depth": None,
                    "min_samples_split": 2,
                },
                description="Simple decision tree classifier",
            )
        )

        self.register(
            ModelDefinition(
                name="SVM Classifier",
                family=ModelFamily.SKLEARN,
                class_ref=SVC,
                task_types=[TaskType.CLASSIFICATION],
                default_hyperparameters={
                    "kernel": "rbf",
                    "C": 1.0,
                    "probability": True,
                },
                description="Support Vector Machine classifier",
            )
        )

        self.register(
            ModelDefinition(
                name="K-Nearest Neighbors Classifier",
                family=ModelFamily.SKLEARN,
                class_ref=KNeighborsClassifier,
                task_types=[TaskType.CLASSIFICATION],
                default_hyperparameters={
                    "n_neighbors": 5,
                    "weights": "uniform",
                },
                description="Instance-based learning classifier",
            )
        )

        self.register(
            ModelDefinition(
                name="Gaussian Naive Bayes",
                family=ModelFamily.SKLEARN,
                class_ref=GaussianNB,
                task_types=[TaskType.CLASSIFICATION],
                default_hyperparameters={},
                description="Probabilistic classifier based on Bayes theorem",
            )
        )

        self.register(
            ModelDefinition(
                name="AdaBoost Classifier",
                family=ModelFamily.SKLEARN,
                class_ref=AdaBoostClassifier,
                task_types=[TaskType.CLASSIFICATION],
                default_hyperparameters={
                    "n_estimators": 50,
                    "learning_rate": 1.0,
                },
                description="Adaptive boosting classifier",
            )
        )

        # Regression models
        self.register(
            ModelDefinition(
                name="Random Forest Regressor",
                family=ModelFamily.SKLEARN,
                class_ref=RandomForestRegressor,
                task_types=[TaskType.REGRESSION],
                default_hyperparameters={
                    "n_estimators": 100,
                    "max_depth": None,
                    "min_samples_split": 2,
                    "n_jobs": -1,
                },
                description="Ensemble of decision trees for regression",
            )
        )

        self.register(
            ModelDefinition(
                name="Gradient Boosting Regressor",
                family=ModelFamily.SKLEARN,
                class_ref=GradientBoostingRegressor,
                task_types=[TaskType.REGRESSION],
                default_hyperparameters={
                    "n_estimators": 100,
                    "learning_rate": 0.1,
                    "max_depth": 3,
                },
                description="Sequential ensemble for regression",
            )
        )

        self.register(
            ModelDefinition(
                name="XGBoost Regressor",
                family=ModelFamily.XGBOOST,
                class_ref=XGBRegressor,
                task_types=[TaskType.REGRESSION],
                default_hyperparameters={
                    "n_estimators": 100,
                    "learning_rate": 0.1,
                    "max_depth": 6,
                },
                description="Optimized gradient boosting for regression",
            )
        )

        self.register(
            ModelDefinition(
                name="LightGBM Regressor",
                family=ModelFamily.LIGHTGBM,
                class_ref=LGBMRegressor,
                task_types=[TaskType.REGRESSION],
                default_hyperparameters={
                    "n_estimators": 100,
                    "learning_rate": 0.1,
                    "max_depth": -1,
                    "num_leaves": 31,
                    "verbosity": -1,
                },
                description="Fast gradient boosting regressor",
            )
        )

        self.register(
            ModelDefinition(
                name="Ridge Regression",
                family=ModelFamily.SKLEARN,
                class_ref=Ridge,
                task_types=[TaskType.REGRESSION],
                default_hyperparameters={
                    "alpha": 1.0,
                },
                description="Linear regression with L2 regularization",
            )
        )

        self.register(
            ModelDefinition(
                name="Lasso Regression",
                family=ModelFamily.SKLEARN,
                class_ref=Lasso,
                task_types=[TaskType.REGRESSION],
                default_hyperparameters={
                    "alpha": 1.0,
                    "max_iter": 1000,
                },
                description="Linear regression with L1 regularization",
            )
        )

        self.register(
            ModelDefinition(
                name="ElasticNet",
                family=ModelFamily.SKLEARN,
                class_ref=ElasticNet,
                task_types=[TaskType.REGRESSION],
                default_hyperparameters={
                    "alpha": 1.0,
                    "l1_ratio": 0.5,
                    "max_iter": 1000,
                },
                description="Linear regression with combined L1/L2 regularization",
            )
        )

        self.register(
            ModelDefinition(
                name="Decision Tree Regressor",
                family=ModelFamily.SKLEARN,
                class_ref=DecisionTreeRegressor,
                task_types=[TaskType.REGRESSION],
                default_hyperparameters={
                    "max_depth": None,
                    "min_samples_split": 2,
                },
                description="Simple decision tree regressor",
            )
        )

        self.register(
            ModelDefinition(
                name="SVM Regressor",
                family=ModelFamily.SKLEARN,
                class_ref=SVR,
                task_types=[TaskType.REGRESSION],
                default_hyperparameters={
                    "kernel": "rbf",
                    "C": 1.0,
                },
                description="Support Vector Machine regressor",
            )
        )

        self.register(
            ModelDefinition(
                name="K-Nearest Neighbors Regressor",
                family=ModelFamily.SKLEARN,
                class_ref=KNeighborsRegressor,
                task_types=[TaskType.REGRESSION],
                default_hyperparameters={
                    "n_neighbors": 5,
                    "weights": "uniform",
                },
                description="Instance-based learning regressor",
            )
        )

    def register(self, definition: ModelDefinition) -> None:
        """
        Register a model definition in the catalogue.

        Args:
            definition: Model definition to register
        """
        # Create a unique key from name (lowercase, spaces to underscores)
        key = definition.name.lower().replace(" ", "_")
        self._models[key] = definition

    def get(self, name: str) -> ModelDefinition | None:
        """
        Get a model definition by name.

        Args:
            name: Model name (case-insensitive, spaces allowed)

        Returns:
            ModelDefinition if found, None otherwise
        """
        key = name.lower().replace(" ", "_")
        return self._models.get(key)

    def list_all(self) -> list[ModelDefinition]:
        """
        List all registered models.

        Returns:
            List of all model definitions
        """
        return list(self._models.values())

    def list_by_task_type(self, task_type: TaskType) -> list[ModelDefinition]:
        """
        List models supporting a specific task type.

        Args:
            task_type: Task type to filter by

        Returns:
            List of model definitions supporting the task type
        """
        return [model for model in self._models.values() if task_type in model.task_types]

    def list_by_family(self, family: ModelFamily) -> list[ModelDefinition]:
        """
        List models from a specific family.

        Args:
            family: Model family to filter by

        Returns:
            List of model definitions from the family
        """
        return [model for model in self._models.values() if model.family == family]

    def get_default_models_for_task(
        self,
        task_type: TaskType,
        max_models: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        Get default model configurations for a task type.

        Returns a curated list of recommended models with their
        default configurations, suitable for auto-selection.

        Args:
            task_type: Task type (classification, regression)
            max_models: Maximum number of models to return

        Returns:
            List of model configuration dictionaries
        """
        # Curated order: best general-purpose models first
        if task_type == TaskType.CLASSIFICATION:
            priority_order = [
                "xgboost_classifier",
                "lightgbm_classifier",
                "random_forest_classifier",
                "gradient_boosting_classifier",
                "logistic_regression",
            ]
        elif task_type == TaskType.REGRESSION:
            priority_order = [
                "xgboost_regressor",
                "lightgbm_regressor",
                "random_forest_regressor",
                "gradient_boosting_regressor",
                "ridge_regression",
            ]
        else:
            priority_order = []

        configs = []
        for key in priority_order:
            if key in self._models:
                model_def = self._models[key]
                configs.append(
                    {
                        "name": model_def.name,
                        "family": model_def.family.value,
                        "class_name": model_def.name,
                        "hyperparameters": model_def.default_hyperparameters.copy(),
                        "enabled": True,
                    }
                )

        if max_models:
            configs = configs[:max_models]

        return configs

    def instantiate_model(
        self,
        name: str,
        hyperparameters: dict[str, Any] | None = None,
        random_seed: int = 42,
    ) -> Any:
        """
        Instantiate a model by name.

        Args:
            name: Model name
            hyperparameters: Hyperparameters to use (overrides defaults)
            random_seed: Random seed for reproducibility

        Returns:
            Instantiated model object

        Raises:
            ValueError: If model not found in catalogue
        """
        definition = self.get(name)
        if definition is None:
            raise ValueError(f"Model '{name}' not found in catalogue")
        return definition.instantiate(hyperparameters, random_seed)


# Global catalogue instance
_catalogue: ModelCatalogue | None = None


def get_catalogue() -> ModelCatalogue:
    """
    Get the global model catalogue instance.

    Returns:
        ModelCatalogue singleton instance
    """
    global _catalogue
    if _catalogue is None:
        _catalogue = ModelCatalogue()
    return _catalogue
