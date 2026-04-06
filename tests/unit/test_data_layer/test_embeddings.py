# tests/unit/test_data_layer/test_embeddings.py
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest


class TestEmbeddingService:
    def test_health_check_returns_true_when_healthy(self):
        """Health check should return True when ChromaDB is reachable."""
        with patch("chromadb.HttpClient") as MockClient:
            mock_client = MagicMock()
            mock_client.heartbeat.return_value = True
            MockClient.return_value = mock_client

            from backend.app.data_layer.embeddings import EmbeddingService

            service = EmbeddingService(host="localhost", port=8000)
            service.client = mock_client

            assert service.health_check() is True

    def test_health_check_returns_false_on_error(self):
        """Health check should return False when ChromaDB is unreachable."""
        with patch("chromadb.HttpClient") as MockClient:
            mock_client = MagicMock()
            mock_client.heartbeat.side_effect = Exception("Connection refused")
            MockClient.return_value = mock_client

            from backend.app.data_layer.embeddings import EmbeddingService

            service = EmbeddingService(host="localhost", port=8000)
            service.client = mock_client

            assert service.health_check() is False

    def test_create_collection_returns_name(self):
        """Create collection should return collection name."""
        with patch("chromadb.HttpClient") as MockClient:
            mock_client = MagicMock()
            mock_collection = MagicMock()
            mock_client.get_or_create_collection.return_value = mock_collection
            MockClient.return_value = mock_client

            from backend.app.data_layer.embeddings import EmbeddingService

            service = EmbeddingService(host="localhost", port=8000)
            service.client = mock_client

            dataset_id = uuid4()
            result = service.create_collection(dataset_id, version=1)

            assert f"dataset_{dataset_id}_v1" == result

    def test_index_documents_validates_length(self):
        """Index documents should validate that documents and IDs have same length."""
        with patch("chromadb.HttpClient") as MockClient:
            mock_client = MagicMock()
            MockClient.return_value = mock_client

            from backend.app.data_layer.embeddings import EmbeddingError, EmbeddingService

            service = EmbeddingService(host="localhost", port=8000)
            service.client = mock_client

            with pytest.raises(EmbeddingError, match="same length"):
                service.index_documents(
                    collection_name="test",
                    documents=["doc1", "doc2"],
                    ids=["id1"],  # Mismatched length
                )

    def test_get_collection_count(self):
        """Get collection count should return document count."""
        with patch("chromadb.HttpClient") as MockClient:
            mock_client = MagicMock()
            mock_collection = MagicMock()
            mock_collection.count.return_value = 42
            mock_client.get_collection.return_value = mock_collection
            MockClient.return_value = mock_client

            from backend.app.data_layer.embeddings import EmbeddingService

            service = EmbeddingService(host="localhost", port=8000)
            service.client = mock_client

            count = service.get_collection_count("test_collection")

            assert count == 42
