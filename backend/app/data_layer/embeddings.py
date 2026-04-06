# backend/app/data_layer/embeddings.py
import uuid
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings

from backend.app.core.config import settings
from backend.app.core.logging import get_logger

logger = get_logger(__name__)


class EmbeddingError(Exception):
    """Raised when embedding operations fail."""

    pass


class EmbeddingService:
    """Service for vector indexing with ChromaDB."""

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
    ) -> None:
        """Initialize ChromaDB client.

        Args:
            host: ChromaDB server host.
            port: ChromaDB server port.
        """
        self.host = host or settings.chroma_host
        self.port = port or settings.chroma_port

        self.client = chromadb.HttpClient(
            host=self.host,
            port=self.port,
            settings=ChromaSettings(anonymized_telemetry=False),
        )

    def health_check(self) -> bool:
        """Check if ChromaDB is reachable.

        Returns:
            True if ChromaDB is healthy.
        """
        try:
            self.client.heartbeat()
            return True
        except Exception as e:
            logger.error("chromadb_health_check_failed", error=str(e))
            return False

    def create_collection(
        self,
        dataset_id: uuid.UUID,
        version: int,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Create a ChromaDB collection for a dataset version.

        Args:
            dataset_id: Dataset UUID.
            version: Version number.
            metadata: Optional collection metadata.

        Returns:
            Collection name/ID.
        """
        collection_name = f"dataset_{dataset_id}_v{version}"

        try:
            collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata=metadata or {"dataset_id": str(dataset_id), "version": version},
            )
            logger.info("collection_created", collection_name=collection_name)
            return collection_name
        except Exception as e:
            logger.error("collection_creation_failed", collection_name=collection_name, error=str(e))
            raise EmbeddingError(f"Failed to create collection: {e}") from e

    def index_documents(
        self,
        collection_name: str,
        documents: list[str],
        ids: list[str],
        metadatas: list[dict[str, Any]] | None = None,
    ) -> int:
        """Index documents into a ChromaDB collection.

        Args:
            collection_name: Target collection name.
            documents: List of text documents to index.
            ids: Unique IDs for each document.
            metadatas: Optional metadata for each document.

        Returns:
            Number of documents indexed.

        Raises:
            EmbeddingError: If indexing fails.
        """
        if len(documents) != len(ids):
            raise EmbeddingError("Documents and IDs must have same length")

        try:
            collection = self.client.get_collection(collection_name)

            batch_size = 100
            total_indexed = 0

            for i in range(0, len(documents), batch_size):
                batch_docs = documents[i : i + batch_size]
                batch_ids = ids[i : i + batch_size]
                batch_meta = metadatas[i : i + batch_size] if metadatas else None

                collection.add(
                    documents=batch_docs,
                    ids=batch_ids,
                    metadatas=batch_meta,
                )
                total_indexed += len(batch_docs)

            logger.info(
                "documents_indexed",
                collection_name=collection_name,
                count=total_indexed,
            )
            return total_indexed

        except Exception as e:
            logger.error("indexing_failed", collection_name=collection_name, error=str(e))
            raise EmbeddingError(f"Failed to index documents: {e}") from e

    def query(
        self,
        collection_name: str,
        query_texts: list[str],
        n_results: int = 5,
        where: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Query a collection for similar documents.

        Args:
            collection_name: Collection to query.
            query_texts: List of query strings.
            n_results: Number of results per query.
            where: Optional filter conditions.

        Returns:
            Query results with documents, distances, and metadata.
        """
        try:
            collection = self.client.get_collection(collection_name)
            results = collection.query(
                query_texts=query_texts,
                n_results=n_results,
                where=where,
            )
            return results
        except Exception as e:
            logger.error("query_failed", collection_name=collection_name, error=str(e))
            raise EmbeddingError(f"Query failed: {e}") from e

    def delete_collection(self, collection_name: str) -> None:
        """Delete a ChromaDB collection.

        Args:
            collection_name: Collection to delete.
        """
        try:
            self.client.delete_collection(collection_name)
            logger.info("collection_deleted", collection_name=collection_name)
        except Exception as e:
            logger.warning("collection_delete_failed", collection_name=collection_name, error=str(e))

    def get_collection_count(self, collection_name: str) -> int:
        """Get the number of documents in a collection.

        Args:
            collection_name: Collection name.

        Returns:
            Document count.
        """
        try:
            collection = self.client.get_collection(collection_name)
            return collection.count()
        except Exception:
            return 0


_embedding_service: EmbeddingService | None = None


def get_embedding_service() -> EmbeddingService:
    """Get or create the singleton embedding service.

    Returns:
        EmbeddingService instance.
    """
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
