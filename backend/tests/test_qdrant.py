"""Tests for Qdrant service."""
import pytest
from unittest.mock import patch, MagicMock

from app.services.qdrant import QdrantService
from app.config import Settings


class TestQdrantService:
    """Test suite for QdrantService."""

    def test_is_configured_false(self):
        """Test is_configured returns False when not configured."""
        settings = Settings(qdrant_url="", openai_api_key="")
        service = QdrantService(settings)
        assert service.is_configured() is False

    def test_is_configured_partial(self):
        """Test is_configured returns False with partial config."""
        settings = Settings(qdrant_url="http://localhost:6333", openai_api_key="")
        service = QdrantService(settings)
        assert service.is_configured() is False

    def test_is_configured_true(self):
        """Test is_configured returns True when fully configured."""
        settings = Settings(
            qdrant_url="http://localhost:6333",
            openai_api_key="sk-test-key"
        )
        service = QdrantService(settings)
        assert service.is_configured() is True

    def test_condition_id_to_point_id(self):
        """Test condition ID to UUID conversion."""
        settings = Settings(qdrant_url="http://localhost:6333", openai_api_key="sk-test")
        service = QdrantService(settings)

        # Should produce consistent UUIDs
        point_id1 = service._condition_id_to_point_id("0x123abc")
        point_id2 = service._condition_id_to_point_id("0x123abc")
        assert point_id1 == point_id2

        # Different condition IDs should produce different UUIDs
        point_id3 = service._condition_id_to_point_id("0x456def")
        assert point_id1 != point_id3

        # Should be valid UUID format
        parts = point_id1.split("-")
        assert len(parts) == 5
        assert len(parts[0]) == 8
        assert len(parts[1]) == 4
        assert len(parts[2]) == 4
        assert len(parts[3]) == 4
        assert len(parts[4]) == 12

    @patch("app.services.qdrant.client.OpenAI")
    @patch("app.services.qdrant.client.QdrantClient")
    def test_get_embedding(self, mock_qdrant_class, mock_openai_class):
        """Test getting embeddings from OpenAI."""
        mock_embedding = [0.1] * 1536
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=mock_embedding)]

        mock_openai = MagicMock()
        mock_openai.embeddings.create.return_value = mock_response
        mock_openai_class.return_value = mock_openai

        mock_qdrant = MagicMock()
        mock_qdrant.get_collections.return_value.collections = []
        mock_qdrant_class.return_value = mock_qdrant

        settings = Settings(
            qdrant_url="http://localhost:6333",
            openai_api_key="sk-test"
        )
        service = QdrantService(settings)
        embedding = service._get_embedding("Test text")

        assert len(embedding) == 1536
        mock_openai.embeddings.create.assert_called_once()

    @patch("app.services.qdrant.client.OpenAI")
    @patch("app.services.qdrant.client.QdrantClient")
    def test_upsert_market(self, mock_qdrant_class, mock_openai_class):
        """Test upserting a single market."""
        mock_embedding = [0.1] * 1536
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=mock_embedding)]

        mock_openai = MagicMock()
        mock_openai.embeddings.create.return_value = mock_response
        mock_openai_class.return_value = mock_openai

        mock_qdrant = MagicMock()
        mock_qdrant.get_collections.return_value.collections = []
        mock_qdrant_class.return_value = mock_qdrant

        settings = Settings(
            qdrant_url="http://localhost:6333",
            openai_api_key="sk-test"
        )
        service = QdrantService(settings)

        result = service.upsert_market(
            condition_id="0x123",
            question="Will Bitcoin reach $100k?",
            description="This market tracks BTC price.",
        )

        assert result is True
        mock_qdrant.upsert.assert_called_once()

    @patch("app.services.qdrant.client.OpenAI")
    @patch("app.services.qdrant.client.QdrantClient")
    def test_upsert_markets_batch(self, mock_qdrant_class, mock_openai_class):
        """Test batch upserting markets."""
        mock_embedding = [0.1] * 1536
        mock_response = MagicMock()
        mock_response.data = [
            MagicMock(embedding=mock_embedding),
            MagicMock(embedding=mock_embedding),
        ]

        mock_openai = MagicMock()
        mock_openai.embeddings.create.return_value = mock_response
        mock_openai_class.return_value = mock_openai

        mock_qdrant = MagicMock()
        mock_qdrant.get_collections.return_value.collections = []
        mock_qdrant_class.return_value = mock_qdrant

        settings = Settings(
            qdrant_url="http://localhost:6333",
            openai_api_key="sk-test"
        )
        service = QdrantService(settings)

        markets = [
            {"conditionId": "0x1", "question": "Market 1"},
            {"conditionId": "0x2", "question": "Market 2"},
        ]

        count = service.upsert_markets_batch(markets, batch_size=10)

        assert count == 2
        mock_qdrant.upsert.assert_called_once()

    @patch("app.services.qdrant.client.OpenAI")
    @patch("app.services.qdrant.client.QdrantClient")
    def test_search(self, mock_qdrant_class, mock_openai_class):
        """Test semantic search."""
        mock_embedding = [0.1] * 1536
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=mock_embedding)]

        mock_openai = MagicMock()
        mock_openai.embeddings.create.return_value = mock_response
        mock_openai_class.return_value = mock_openai

        mock_hit = MagicMock()
        mock_hit.payload = {"condition_id": "0x1", "question": "Bitcoin market"}
        mock_hit.score = 0.85

        mock_qdrant = MagicMock()
        mock_qdrant.get_collections.return_value.collections = []
        mock_qdrant.search.return_value = [mock_hit]
        mock_qdrant_class.return_value = mock_qdrant

        settings = Settings(
            qdrant_url="http://localhost:6333",
            openai_api_key="sk-test"
        )
        service = QdrantService(settings)

        results = service.search("Bitcoin price prediction")

        assert len(results) == 1
        assert results[0]["condition_id"] == "0x1"
        assert results[0]["similarity_score"] == 0.85

    @patch("app.services.qdrant.client.OpenAI")
    @patch("app.services.qdrant.client.QdrantClient")
    def test_delete_market(self, mock_qdrant_class, mock_openai_class):
        """Test deleting a market."""
        mock_openai_class.return_value = MagicMock()

        mock_qdrant = MagicMock()
        mock_qdrant.get_collections.return_value.collections = []
        mock_qdrant_class.return_value = mock_qdrant

        settings = Settings(
            qdrant_url="http://localhost:6333",
            openai_api_key="sk-test"
        )
        service = QdrantService(settings)

        result = service.delete_market("0x123")

        assert result is True
        mock_qdrant.delete.assert_called_once()

    @patch("app.services.qdrant.client.OpenAI")
    @patch("app.services.qdrant.client.QdrantClient")
    def test_get_collection_info(self, mock_qdrant_class, mock_openai_class):
        """Test getting collection info."""
        mock_openai_class.return_value = MagicMock()

        mock_info = MagicMock()
        mock_info.vectors_count = 1000
        mock_info.points_count = 1000
        mock_info.status = "green"

        mock_qdrant = MagicMock()
        mock_qdrant.get_collections.return_value.collections = []
        mock_qdrant.get_collection.return_value = mock_info
        mock_qdrant_class.return_value = mock_qdrant

        settings = Settings(
            qdrant_url="http://localhost:6333",
            openai_api_key="sk-test"
        )
        service = QdrantService(settings)

        info = service.get_collection_info()

        assert info["vectors_count"] == 1000
        assert info["points_count"] == 1000

    @patch("app.services.qdrant.client.OpenAI")
    @patch("app.services.qdrant.client.QdrantClient")
    def test_clear_collection(self, mock_qdrant_class, mock_openai_class):
        """Test clearing collection."""
        mock_openai_class.return_value = MagicMock()

        mock_qdrant = MagicMock()
        mock_qdrant.get_collections.return_value.collections = []
        mock_qdrant_class.return_value = mock_qdrant

        settings = Settings(
            qdrant_url="http://localhost:6333",
            openai_api_key="sk-test"
        )
        service = QdrantService(settings)

        result = service.clear_collection()

        assert result is True
        mock_qdrant.delete_collection.assert_called_once()


class TestQdrantRoutes:
    """Test suite for Qdrant API routes."""

    @pytest.mark.asyncio
    async def test_qdrant_status_not_configured(self, client):
        """Test /api/markets/qdrant/status when not configured."""
        response = await client.get("/api/markets/qdrant/status")
        assert response.status_code == 200
        data = response.json()
        assert data["configured"] is False

    @pytest.mark.asyncio
    async def test_semantic_search_not_configured(self, client):
        """Test /api/markets/semantic-search when not configured."""
        response = await client.get("/api/markets/semantic-search?q=bitcoin")
        assert response.status_code == 503

    @pytest.mark.asyncio
    async def test_embed_markets_not_configured(self, client):
        """Test /api/markets/qdrant/embed when not configured."""
        response = await client.post("/api/markets/qdrant/embed")
        assert response.status_code == 503

    @pytest.mark.asyncio
    async def test_clear_qdrant_requires_confirm(self, client):
        """Test /api/markets/qdrant/clear requires confirmation."""
        response = await client.delete("/api/markets/qdrant/clear")
        assert response.status_code == 400
