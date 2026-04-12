# backend/app/models/experiment.py
"""
Experiment models — SQLAlchemy ORM + Pydantic schemas.

Defines the data structures for experiment runs, model configurations,
and result tracking.
"""

import enum
import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, Float, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base, TimestampMixin


class ExperimentStatus(str, enum.Enum):
    """Status of an experiment run."""

    PENDING = "pending"
    VALIDATING = "validating"
    PREPARING = "preparing"
    RUNNING = "running"
    EVALUATING = "evaluating"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExperimentType(str, enum.Enum):
    """Type of experiment based on model/task category."""

    TABULAR_ML = "tabular_ml"
    NLP = "nlp"
    LLM = "llm"
    RAG = "rag"
    AGENT = "agent"


class TaskType(str, enum.Enum):
    """ML task type for tabular experiments."""

    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    CLUSTERING = "clustering"


class ModelFamily(str, enum.Enum):
    """Model family for categorization."""

    SKLEARN = "sklearn"
    XGBOOST = "xgboost"
    LIGHTGBM = "lightgbm"
    CATBOOST = "catboost"
    HUGGINGFACE = "huggingface"
    OPENAI = "openai"
    LOCAL_LLM = "local_llm"
    CUSTOM = "custom"


# =============================================================================
# SQLAlchemy Models
# =============================================================================


class Experiment(Base, TimestampMixin):
    """SQLAlchemy model for experiment runs."""

    __tablename__ = "experiments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    experiment_type: Mapped[ExperimentType] = mapped_column(
        Enum(ExperimentType),
        nullable=False,
        default=ExperimentType.TABULAR_ML,
    )
    task_type: Mapped[TaskType | None] = mapped_column(
        Enum(TaskType),
        nullable=True,
    )
    status: Mapped[ExperimentStatus] = mapped_column(
        Enum(ExperimentStatus),
        nullable=False,
        default=ExperimentStatus.PENDING,
    )
    dataset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("datasets.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    dataset_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dataset_versions.id", ondelete="SET NULL"),
        nullable=True,
    )
    target_column: Mapped[str | None] = mapped_column(String(255), nullable=True)
    feature_columns: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    models_config: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    constraints: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    mlflow_experiment_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    mlflow_run_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    random_seed: Mapped[int] = mapped_column(Integer, nullable=False, default=42)
    owner_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    results: Mapped[list["ExperimentResult"]] = relationship(
        "ExperimentResult",
        back_populates="experiment",
        cascade="all, delete-orphan",
    )


class ExperimentResult(Base, TimestampMixin):
    """SQLAlchemy model for individual model results within an experiment."""

    __tablename__ = "experiment_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    experiment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("experiments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    model_name: Mapped[str] = mapped_column(String(255), nullable=False)
    model_family: Mapped[ModelFamily] = mapped_column(
        Enum(ModelFamily),
        nullable=False,
    )
    model_config: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    hyperparameters: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    metrics: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    global_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    training_duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    inference_latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    artefact_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    mlflow_run_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    experiment: Mapped["Experiment"] = relationship("Experiment", back_populates="results")


# =============================================================================
# Pydantic Schemas
# =============================================================================


class ModelConfig(BaseModel):
    """Configuration for a single model to run in an experiment."""

    name: str = Field(..., description="Display name for the model")
    family: ModelFamily = Field(..., description="Model family (sklearn, xgboost, etc.)")
    class_name: str = Field(..., description="Full class name (e.g., 'RandomForestClassifier')")
    hyperparameters: dict[str, Any] = Field(default_factory=dict, description="Model hyperparameters")
    enabled: bool = Field(default=True, description="Whether to include this model in the run")


class ExperimentConstraints(BaseModel):
    """Constraints for experiment execution and model selection."""

    max_training_time_seconds: float | None = Field(None, description="Max training time per model")
    max_models: int | None = Field(None, description="Maximum number of models to evaluate")
    min_accuracy: float | None = Field(None, ge=0.0, le=1.0, description="Minimum accuracy threshold")
    max_latency_ms: float | None = Field(None, description="Maximum inference latency")


class ExperimentCreate(BaseModel):
    """Schema for creating a new experiment."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    experiment_type: ExperimentType = ExperimentType.TABULAR_ML
    task_type: TaskType | None = None
    dataset_id: uuid.UUID
    dataset_version_id: uuid.UUID | None = None
    target_column: str | None = None
    feature_columns: list[str] | None = None
    models: list[ModelConfig] = Field(default_factory=list, description="Models to evaluate")
    constraints: ExperimentConstraints | None = None
    random_seed: int = Field(42, ge=0)


class ExperimentRead(BaseModel):
    """Schema for reading experiment info."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None
    experiment_type: ExperimentType
    task_type: TaskType | None
    status: ExperimentStatus
    owner_id: uuid.UUID | None
    dataset_id: uuid.UUID | None
    dataset_version_id: uuid.UUID | None
    target_column: str | None
    feature_columns: list[str] | None
    models_config: dict[str, Any]
    constraints: dict[str, Any] | None
    mlflow_experiment_id: str | None
    mlflow_run_id: str | None
    random_seed: int
    started_at: datetime | None
    completed_at: datetime | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime


class ExperimentResultRead(BaseModel):
    """Schema for reading experiment result info."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    experiment_id: uuid.UUID
    model_name: str
    model_family: ModelFamily
    model_config: dict[str, Any]
    hyperparameters: dict[str, Any] | None
    metrics: dict[str, Any]
    global_score: float | None
    rank: int | None
    training_duration_seconds: float | None
    inference_latency_ms: float | None
    artefact_path: str | None
    mlflow_run_id: str | None
    error_message: str | None
    created_at: datetime


class ExperimentSummary(BaseModel):
    """Summary of experiment results for reporting."""

    experiment_id: uuid.UUID
    experiment_name: str
    status: ExperimentStatus
    total_models: int
    successful_models: int
    failed_models: int
    best_model_name: str | None
    best_model_score: float | None
    recommendation: str | None
    duration_seconds: float | None


class ExperimentListResponse(BaseModel):
    """Schema for paginated experiment list response."""

    items: list[ExperimentRead]
    total: int
    page: int
    page_size: int
