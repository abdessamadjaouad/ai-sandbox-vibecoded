# backend/app/api/datasets/routes.py
import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db_session
from backend.app.core.logging import get_logger
from backend.app.data_layer.embeddings import EmbeddingService, get_embedding_service
from backend.app.data_layer.ingestion import DatasetIngestionService, IngestionError
from backend.app.data_layer.storage import StorageClient, get_storage_client
from backend.app.data_layer.validation import DatasetValidationService
from backend.app.data_layer.versioning import DatasetVersioningService, VersioningError
from backend.app.models.dataset import (
    Dataset,
    DatasetAutoConfigRead,
    DatasetCreate,
    DatasetListResponse,
    DatasetRead,
    DatasetStatus,
    DatasetType,
    DatasetVersion,
    DatasetVersionCreate,
    DatasetVersionRead,
    ValidationReport,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/datasets", tags=["datasets"])


def _guess_task_type(df, target_column: str | None) -> tuple[str, str, str]:
    """Infer task type from the probable target column.

    Returns:
        tuple of (task_type, confidence, rationale)
    """
    if not target_column or target_column not in df.columns:
        return "classification", "low", "No clear target was detected, defaulted to classification."

    series = df[target_column].dropna()
    if series.empty:
        return "classification", "low", f"Target column '{target_column}' is empty, defaulted to classification."

    dtype = str(series.dtype).lower()
    unique_values = int(series.nunique())
    sample_size = int(len(series))

    if any(token in dtype for token in ("object", "string", "bool", "category")):
        return (
            "classification",
            "high",
            f"Target column '{target_column}' is categorical ({dtype}), so classification is recommended.",
        )

    if unique_values <= min(20, max(2, int(sample_size * 0.15))):
        return (
            "classification",
            "medium",
            f"Target column '{target_column}' has only {unique_values} distinct values, so classification is likely.",
        )

    return (
        "regression",
        "high",
        f"Target column '{target_column}' is numeric with {unique_values} distinct values, so regression is recommended.",
    )


def _suggest_target_column(columns: list[str], dtypes: dict[str, str]) -> tuple[str | None, str]:
    """Suggest a likely target column by name and type heuristics."""
    if not columns:
        return None, "No columns were found in the dataset."

    preferred = [
        "target",
        "label",
        "class",
        "outcome",
        "y",
        "default",
        "risk",
        "churn",
        "fraud",
        "approved",
        "prediction",
    ]
    normalized = {col.lower(): col for col in columns}
    for keyword in preferred:
        if keyword in normalized:
            return normalized[
                keyword
            ], f"Column '{normalized[keyword]}' matched common target naming pattern '{keyword}'."

    candidate = columns[-1]
    candidate_dtype = dtypes.get(candidate, "unknown")
    return candidate, f"No explicit target keyword found; selected last column '{candidate}' ({candidate_dtype})."


def _normalize_dataset_name(name: str) -> str:
    """Normalize a human-readable dataset name from text source."""
    compact = " ".join(name.replace("_", " ").replace("-", " ").split())
    if not compact:
        return "Dataset"
    return compact[:255]


def get_ingestion_service(
    storage: Annotated[StorageClient, Depends(get_storage_client)],
) -> DatasetIngestionService:
    """Dependency for ingestion service."""
    return DatasetIngestionService(storage)


def get_validation_service() -> DatasetValidationService:
    """Dependency for validation service."""
    return DatasetValidationService()


def get_versioning_service(
    storage: Annotated[StorageClient, Depends(get_storage_client)],
) -> DatasetVersioningService:
    """Dependency for versioning service."""
    return DatasetVersioningService(storage)


@router.post("", response_model=DatasetRead, status_code=status.HTTP_201_CREATED)
async def upload_dataset(
    file: Annotated[UploadFile, File(description="Dataset file (CSV, JSON, Parquet, Excel)")],
    name: Annotated[str | None, Form(description="Dataset name")] = None,
    description: Annotated[str | None, Form(description="Dataset description")] = None,
    db: AsyncSession = Depends(get_db_session),
    ingestion: DatasetIngestionService = Depends(get_ingestion_service),
    validation: DatasetValidationService = Depends(get_validation_service),
) -> Dataset:
    """Upload and ingest a new dataset.

    - Parses the file and extracts schema information
    - Stores the raw file in MinIO
    - Validates the dataset quality
    - Creates a database record
    """
    dataset_id = uuid.uuid4()

    try:
        result = ingestion.ingest_file(file.file, file.filename or "unknown", dataset_id)
    except IngestionError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    dataset_type = ingestion.detect_dataset_type(result["schema_info"])

    df = ingestion.load_dataframe(result["file_path"], result["file_format"])
    validation_report = validation.validate(df)

    detected_name = _normalize_dataset_name(Path(file.filename or "dataset").stem)
    final_name = _normalize_dataset_name(name) if name else detected_name

    dataset = Dataset(
        id=dataset_id,
        name=final_name,
        description=description,
        dataset_type=dataset_type,
        status=DatasetStatus.VALIDATED if validation_report.is_valid else DatasetStatus.FAILED,
        file_path=result["file_path"],
        file_size_bytes=result["file_size_bytes"],
        file_format=result["file_format"],
        row_count=result["row_count"],
        column_count=result["column_count"],
        schema_info=result["schema_info"],
        validation_report=validation_report.model_dump(),
    )

    db.add(dataset)
    await db.flush()

    logger.info("dataset_uploaded", dataset_id=str(dataset_id), name=final_name, status=dataset.status.value)

    return dataset


@router.get("/{dataset_id}/autoconfig", response_model=DatasetAutoConfigRead)
async def get_dataset_auto_config(
    dataset_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    ingestion: DatasetIngestionService = Depends(get_ingestion_service),
) -> DatasetAutoConfigRead:
    """Return auto-detected configuration for a dataset.

    The endpoint proposes a target column, feature columns, task type,
    and stratify suggestion for non-technical users.
    """
    result = await db.execute(select(Dataset).where(Dataset.id == dataset_id))
    dataset = result.scalar_one_or_none()

    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")

    try:
        df = ingestion.load_dataframe(dataset.file_path, dataset.file_format)
    except IngestionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unable to inspect dataset: {exc}")

    columns = [str(c) for c in list(df.columns)]
    dtypes = {str(col): str(dtype) for col, dtype in df.dtypes.items()}
    target_column, target_rationale = _suggest_target_column(columns, dtypes)
    task_type, confidence, task_rationale = _guess_task_type(df, target_column)

    feature_columns = [col for col in columns if col != target_column]
    stratify_column = target_column if task_type == "classification" and target_column else None
    suggested_name = _normalize_dataset_name(dataset.name)

    return DatasetAutoConfigRead(
        dataset_id=dataset.id,
        suggested_name=suggested_name,
        task_type=task_type,
        target_column=target_column,
        feature_columns=feature_columns,
        stratify_column=stratify_column,
        confidence=confidence,
        rationale=f"{target_rationale} {task_rationale}",
    )


@router.get("", response_model=DatasetListResponse)
async def list_datasets(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    status_filter: DatasetStatus | None = None,
    type_filter: DatasetType | None = None,
    db: AsyncSession = Depends(get_db_session),
) -> DatasetListResponse:
    """List all datasets with pagination and filtering."""
    query = select(Dataset)

    if status_filter:
        query = query.where(Dataset.status == status_filter)
    if type_filter:
        query = query.where(Dataset.dataset_type == type_filter)

    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0

    query = query.offset((page - 1) * page_size).limit(page_size).order_by(Dataset.created_at.desc())

    result = await db.execute(query)
    datasets = result.scalars().all()

    return DatasetListResponse(
        items=[DatasetRead.model_validate(d) for d in datasets],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{dataset_id}", response_model=DatasetRead)
async def get_dataset(
    dataset_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
) -> Dataset:
    """Get a dataset by ID."""
    result = await db.execute(select(Dataset).where(Dataset.id == dataset_id))
    dataset = result.scalar_one_or_none()

    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")

    return dataset


@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dataset(
    dataset_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    storage: StorageClient = Depends(get_storage_client),
) -> None:
    """Delete a dataset and its files."""
    result = await db.execute(select(Dataset).where(Dataset.id == dataset_id))
    dataset = result.scalar_one_or_none()

    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")

    files = storage.list_files(prefix=f"datasets/{dataset_id}/")
    for f in files:
        storage.delete_file(f)

    await db.delete(dataset)

    logger.info("dataset_deleted", dataset_id=str(dataset_id))


@router.get("/{dataset_id}/validation", response_model=ValidationReport)
async def get_validation_report(
    dataset_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
) -> ValidationReport:
    """Get the validation report for a dataset."""
    result = await db.execute(select(Dataset).where(Dataset.id == dataset_id))
    dataset = result.scalar_one_or_none()

    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")

    if not dataset.validation_report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Validation report not available")

    return ValidationReport(**dataset.validation_report)


@router.post("/{dataset_id}/versions", response_model=DatasetVersionRead, status_code=status.HTTP_201_CREATED)
async def create_version(
    dataset_id: uuid.UUID,
    config: DatasetVersionCreate,
    db: AsyncSession = Depends(get_db_session),
    ingestion: DatasetIngestionService = Depends(get_ingestion_service),
    versioning: DatasetVersioningService = Depends(get_versioning_service),
) -> DatasetVersion:
    """Create a new version with train/val/test splits."""
    result = await db.execute(select(Dataset).where(Dataset.id == dataset_id))
    dataset = result.scalar_one_or_none()

    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")

    if dataset.status != DatasetStatus.VALIDATED and dataset.status != DatasetStatus.INDEXED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Dataset must be validated before versioning (current status: {dataset.status.value})",
        )

    version_count = await db.scalar(select(func.count()).where(DatasetVersion.dataset_id == dataset_id))
    new_version_num = (version_count or 0) + 1

    df = ingestion.load_dataframe(dataset.file_path, dataset.file_format)

    try:
        version_result = versioning.create_version(
            df=df,
            dataset_id=dataset_id,
            version=new_version_num,
            train_ratio=config.train_ratio,
            val_ratio=config.val_ratio,
            test_ratio=config.test_ratio,
            random_seed=config.random_seed,
            stratify_column=config.stratify_column,
        )
    except VersioningError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    version = DatasetVersion(
        dataset_id=dataset_id,
        version=new_version_num,
        split_config=version_result["split_config"],
        train_path=version_result["train_path"],
        val_path=version_result["val_path"],
        test_path=version_result["test_path"],
        train_rows=version_result["train_rows"],
        val_rows=version_result["val_rows"],
        test_rows=version_result["test_rows"],
        random_seed=version_result["random_seed"],
        config_hash=version_result["config_hash"],
    )

    db.add(version)
    await db.flush()

    logger.info(
        "dataset_version_created",
        dataset_id=str(dataset_id),
        version=new_version_num,
    )

    return version


@router.get("/{dataset_id}/versions", response_model=list[DatasetVersionRead])
async def list_versions(
    dataset_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
) -> list[DatasetVersion]:
    """List all versions for a dataset."""
    result = await db.execute(select(Dataset).where(Dataset.id == dataset_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")

    result = await db.execute(
        select(DatasetVersion).where(DatasetVersion.dataset_id == dataset_id).order_by(DatasetVersion.version.desc())
    )
    return list(result.scalars().all())


@router.post("/{dataset_id}/versions/{version_id}/index", response_model=DatasetVersionRead)
async def index_version(
    dataset_id: uuid.UUID,
    version_id: uuid.UUID,
    text_column: Annotated[str, Query(description="Column containing text to index")],
    db: AsyncSession = Depends(get_db_session),
    versioning: DatasetVersioningService = Depends(get_versioning_service),
    embedding: EmbeddingService = Depends(get_embedding_service),
) -> DatasetVersion:
    """Index a dataset version in ChromaDB for RAG."""
    result = await db.execute(
        select(DatasetVersion).where(
            DatasetVersion.id == version_id,
            DatasetVersion.dataset_id == dataset_id,
        )
    )
    version = result.scalar_one_or_none()

    if not version:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version not found")

    if version.chroma_collection_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Version already indexed")

    train_df = versioning.load_split(version.train_path)

    if text_column not in train_df.columns:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Column '{text_column}' not found in dataset",
        )

    collection_name = embedding.create_collection(dataset_id, version.version)

    documents = train_df[text_column].dropna().astype(str).tolist()
    ids = [f"doc_{i}" for i in range(len(documents))]

    embedding.index_documents(collection_name, documents, ids)

    version.chroma_collection_id = collection_name
    await db.flush()

    result = await db.execute(select(Dataset).where(Dataset.id == dataset_id))
    dataset = result.scalar_one_or_none()
    if dataset:
        dataset.status = DatasetStatus.INDEXED

    logger.info(
        "dataset_version_indexed",
        dataset_id=str(dataset_id),
        version=version.version,
        collection_name=collection_name,
        documents_indexed=len(documents),
    )

    return version
