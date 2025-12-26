"""Qdrant vector database client for semantic search."""

import hashlib
from typing import Any
import structlog

from ...config import get_settings
from ...core.exceptions import QdrantError
from ..llm.client import OpenAIClient

logger = structlog.get_logger()

# Optional qdrant import
try:
    from qdrant_client import AsyncQdrantClient
    from qdrant_client.models import (
        Distance,
        VectorParams,
        PointStruct,
        Filter,
        FieldCondition,
        MatchValue,
    )
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    AsyncQdrantClient = None


class QdrantService:
    """Service for semantic search using Qdrant vector database."""

    VECTOR_DIM = 1536  # text-embedding-3-small dimension

    def __init__(self) -> None:
        self.settings = get_settings()
        self.openai = OpenAIClient()
        self._client = None

        if not QDRANT_AVAILABLE:
            logger.warning("qdrant_not_installed")
        elif not self.settings.qdrant_configured:
            logger.warning("qdrant_not_configured")

    @property
    def is_available(self) -> bool:
        """Check if Qdrant is available and configured."""
        return QDRANT_AVAILABLE and self.settings.qdrant_configured

    async def _get_client(self) -> "AsyncQdrantClient":
        """Get or create the Qdrant client."""
        if not self.is_available:
            raise QdrantError("Qdrant is not available")

        if self._client is None:
            self._client = AsyncQdrantClient(
                url=self.settings.qdrant_url,
                api_key=self.settings.qdrant_api_key,
            )
        return self._client

    async def ensure_collection(self) -> None:
        """Ensure the collection exists."""
        if not self.is_available:
            return

        client = await self._get_client()
        collections = await client.get_collections()
        collection_names = [c.name for c in collections.collections]

        if self.settings.qdrant_collection not in collection_names:
            await client.create_collection(
                collection_name=self.settings.qdrant_collection,
                vectors_config=VectorParams(
                    size=self.VECTOR_DIM,
                    distance=Distance.COSINE,
                ),
            )
            logger.info("qdrant_collection_created", name=self.settings.qdrant_collection)

    async def upsert_markets(self, markets: list[dict[str, Any]]) -> int:
        """Embed and store markets in Qdrant.

        Args:
            markets: List of market dicts with 'condition_id', 'question', 'description'

        Returns:
            Number of markets upserted
        """
        if not self.is_available or not markets:
            return 0

        await self.ensure_collection()
        client = await self._get_client()

        # Batch embed market texts
        texts = [
            f"{m.get('question', '')} {m.get('description', '')}"
            for m in markets
        ]
        embeddings = await self.openai.embed_batch(texts)

        # Create points
        points = []
        for market, embedding in zip(markets, embeddings):
            point_id = hashlib.md5(market["condition_id"].encode()).hexdigest()
            points.append(PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "condition_id": market["condition_id"],
                    "question": market.get("question", ""),
                    "description": market.get("description"),
                    "category": market.get("category"),
                    "active": market.get("active", True),
                },
            ))

        # Upsert in batches
        batch_size = 100
        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            await client.upsert(
                collection_name=self.settings.qdrant_collection,
                points=batch,
            )

        logger.info("qdrant_upsert_complete", count=len(points))
        return len(points)

    async def search(
        self,
        query: str,
        limit: int = 10,
        score_threshold: float = 0.35,
        active_only: bool = True,
    ) -> list[dict[str, Any]]:
        """Search for relevant markets using semantic similarity.

        Args:
            query: Search query text
            limit: Maximum results
            score_threshold: Minimum similarity score
            active_only: Only return active markets

        Returns:
            List of market payloads sorted by relevance
        """
        if not self.is_available:
            return []

        client = await self._get_client()

        # Embed query
        query_vector = await self.openai.embed(query)

        # Build filter
        query_filter = None
        if active_only:
            query_filter = Filter(
                must=[FieldCondition(key="active", match=MatchValue(value=True))]
            )

        # Search
        results = await client.search(
            collection_name=self.settings.qdrant_collection,
            query_vector=query_vector,
            limit=limit,
            score_threshold=score_threshold,
            query_filter=query_filter,
        )

        return [r.payload for r in results]

    async def close(self) -> None:
        """Close the client."""
        if self._client:
            await self._client.close()
            self._client = None
