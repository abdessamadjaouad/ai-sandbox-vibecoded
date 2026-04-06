# backend/app/models/dataset.py
import enum
import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base, TimestampMixin


class DatasetStatus(str, enum.Enum):
    """Dataset processing status."""

    PENDING = "pending"
    VALIDATING = "validating"
    VALIDATED = "validated"
    FAILED = "failed"
    INDEXED = "indexed"


class DatasetType(str, enum.Enum):
    """Type of dataset based on content."""

    TABULAR = "tabular"
    TEXT = "text"
    IMAGE = "image"
    MIXED = "mixed"


# =============================================================================
# SQLAlchemy Models
# =============================================================================


class Dataset(Base, TimestampMixin):
    """SQLAlchemy model for datasets."""

    __tablename__ = "datasets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    dataset_type: Mapped[DatasetType] = mapped_column(
        Enum(DatasetType),
        nullable=False,
        default=DatasetType.TABULAR,
    )
    status: Mapped[DatasetStatus] = mapped_column(
        Enum(DatasetStatus),
        nullable=False,
        default=DatasetStatus.PENDING,
    )
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    file_format: Mapped[str] = mapped_column(String(50), nullable=False)
    row_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    column_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    schema_info: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    validation_report: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    owner_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    versions: Mapped[list["DatasetVersion"]] = relationship(
        "DatasetVersion",
        back_populates="dataset",
        cascade="all, delete-orphan",
    )


class DatasetVersion(Base, TimestampMixin):
    """SQLAlchemy model for dataset versions (train/val/test splits)."""

    __tablename__ = "dataset_versions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    dataset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    split_config: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    train_path: Mapped[str] = mapped_column(String(512), nullable=False)
    val_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    test_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    train_rows: Mapped[int] = mapped_column(Integer, nullable=False)
    val_rows: Mapped[int | None] = mapped_column(Integer, nullable=True)
    test_rows: Mapped[int | None] = mapped_column(Integer, nullable=True)
    random_seed: Mapped[int] = mapped_column(Integer, nullable=False, default=42)
    config_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    chroma_collection_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    dataset: Mapped["Dataset"] = relationship("Dataset", back_populates="versions")


# =============================================================================
# Pydantic Schemas
# =============================================================================


class DatasetBase(BaseModel):
    """Base schema for dataset operations."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    dataset_type: DatasetType = DatasetType.TABULAR


class DatasetCreate(DatasetBase):
    """Schema for creating a new dataset."""

    pass


class DatasetRead(DatasetBase):
    """Schema for reading dataset info."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: DatasetStatus
    file_path: str
    file_size_bytes: int
    file_format: str
    row_count: int | None = None
    column_count: int | None = None
    schema_info: dict[str, Any] | None = None
    validation_report: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime


class DatasetVersionCreate(BaseModel):
    """Schema for creating a dataset version with split config."""

    train_ratio: float = Field(0.7, ge=0.1, le=0.95)
    val_ratio: float = Field(0.15, ge=0.0, le=0.5)
    test_ratio: float = Field(0.15, ge=0.0, le=0.5)
    random_seed: int = Field(42, ge=0)
    stratify_column: str | None = None


class DatasetVersionRead(BaseModel):
    """Schema for reading dataset version info."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    dataset_id: uuid.UUID
    version: int
    split_config: dict[str, Any]
    train_path: str
    val_path: str | None
    test_path: str | None
    train_rows: int
    val_rows: int | None
    test_rows: int | None
    random_seed: int
    config_hash: str
    chroma_collection_id: str | None
    created_at: datetime


class ValidationReport(BaseModel):
    """Schema for dataset validation report."""

    is_valid: bool
    total_rows: int
    total_columns: int
    null_counts: dict[str, int]
    null_percentages: dict[str, float]
    dtypes: dict[str, str]
    duplicate_rows: int
    issues: list[str]
    warnings: list[str]


class DatasetListResponse(BaseModel):
    """Schema for paginated dataset list response."""

    items: list[DatasetRead]
    total: int
    page: int
    page_size: int
