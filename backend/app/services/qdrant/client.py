"""Qdrant vector database service for semantic market search."""
import hashlib
import json
import logging
from pathlib import Path

from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams, PointStruct

from ...config import Settings, get_settings

logger = logging.getLogger(__name__)

# Settings file path (same as in routes/settings.py)
SETTINGS_FILE = Path("data/settings.json")


def _load_saved_settings() -> dict:
    """Load settings from JSON file."""
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def _get_effective_setting(key: str, env_settings: Settings, saved: dict) -> str:
    """Get effective setting value, preferring saved over env."""
    if key in saved and saved[key]:
        return saved[key]
    return getattr(env_settings, key, "") or ""


class QdrantService:
    """Service for vector-based market search using Qdrant."""

    VECTOR_SIZE = 1536  # text-embedding-3-small dimension

    def __init__(self, settings: Settings | None = None):
        self.env_settings = settings or get_settings()
        self._saved_settings = _load_saved_settings()

        # Get effective settings (saved > env)
        self.qdrant_url = _get_effective_setting("qdrant_url", self.env_settings, self._saved_settings)
        self.qdrant_api_key = _get_effective_setting("qdrant_api_key", self.env_settings, self._saved_settings)
        self.openai_api_key = _get_effective_setting("openai_api_key", self.env_settings, self._saved_settings)
        self.collection_name = _get_effective_setting("qdrant_collection_name", self.env_settings, self._saved_settings) or "polymarket_markets"

        self._client: QdrantClient | None = None
        self._openai: OpenAI | None = None

    @property
    def client(self) -> QdrantClient:
        """Lazy-initialize Qdrant client."""
        if self._client is None:
            if not self.qdrant_url:
                raise ValueError("QDRANT_URL not configured")
            self._client = QdrantClient(
                url=self.qdrant_url,
                api_key=self.qdrant_api_key or None,
            )
            self._ensure_collection()
        return self._client

    @property
    def openai(self) -> OpenAI:
        """Lazy-initialize OpenAI client."""
        if self._openai is None:
            if not self.openai_api_key:
                raise ValueError("OPENAI_API_KEY not configured")
            self._openai = OpenAI(api_key=self.openai_api_key)
        return self._openai

    def _ensure_collection(self):
        """Create collection if it doesn't exist."""
        collections = self._client.get_collections().collections
        exists = any(c.name == self.collection_name for c in collections)

        if not exists:
            self._client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.VECTOR_SIZE,
                    distance=Distance.COSINE,
                ),
            )
            logger.info(f"[QDRANT] Created collection: {self.collection_name}")

    def _get_embedding(self, text: str) -> list[float]:
        """Get embedding vector for text using OpenAI."""
        text = text[:30000]  # Truncate to avoid token limits
        response = self.openai.embeddings.create(
            model=self.env_settings.openai_embedding_model,
            input=text,
        )
        return response.data[0].embedding

    def _condition_id_to_point_id(self, condition_id: str) -> str:
        """Convert condition_id to UUID format for Qdrant."""
        h = hashlib.md5(condition_id.encode()).hexdigest()
        return f"{h[:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}"

    def upsert_market(
        self,
        condition_id: str,
        question: str,
        description: str | None = None,
        metadata: dict | None = None,
    ) -> bool:
        """Embed and store a market in Qdrant."""
        try:
            text = question
            if description:
                text = f"{question}\n\n{description}"

            embedding = self._get_embedding(text)
            point_id = self._condition_id_to_point_id(condition_id)

            payload = {
                "condition_id": condition_id,
                "question": question,
                "description": description or "",
                **(metadata or {}),
            }

            self.client.upsert(
                collection_name=self.collection_name,
                points=[PointStruct(id=point_id, vector=embedding, payload=payload)],
            )
            return True

        except Exception as e:
            logger.error(f"[QDRANT] Upsert error for {condition_id}: {e}")
            return False

    def upsert_markets_batch(self, markets: list[dict], batch_size: int = 100) -> int:
        """Batch upsert multiple markets. Returns count stored."""
        stored = 0
        total = len(markets)

        for i in range(0, total, batch_size):
            batch = markets[i : i + batch_size]
            points = []

            # Prepare texts for batch embedding
            texts = []
            for m in batch:
                text = m.get("question", "")
                if m.get("description"):
                    text = f"{text}\n\n{m['description']}"
                texts.append(text[:30000])

            try:
                # Batch embedding call
                response = self.openai.embeddings.create(
                    model=self.env_settings.openai_embedding_model,
                    input=texts,
                )

                for j, m in enumerate(batch):
                    condition_id = m.get("conditionId") or m.get("condition_id")
                    if not condition_id:
                        continue

                    point_id = self._condition_id_to_point_id(condition_id)
                    embedding = response.data[j].embedding

                    payload = {
                        "condition_id": condition_id,
                        "question": m.get("question", ""),
                        "description": m.get("description", ""),
                        "market_slug": m.get("slug", ""),
                        "end_date_iso": m.get("endDate", ""),
                        "liquidity": m.get("liquidity", 0),
                        "volume": m.get("volume", 0),
                    }

                    points.append(PointStruct(id=point_id, vector=embedding, payload=payload))

                if points:
                    self.client.upsert(collection_name=self.collection_name, points=points)
                    stored += len(points)

                logger.info(f"[QDRANT] Embedded {min(i + batch_size, total)}/{total} markets")

            except Exception as e:
                logger.error(f"[QDRANT] Batch embedding error: {e}")
                continue

        return stored

    def search(
        self,
        query: str,
        limit: int = 10,
        score_threshold: float = 0.3,
    ) -> list[dict]:
        """Search for semantically similar markets."""
        try:
            query_embedding = self._get_embedding(query)

            results = self.client.query_points(
                collection_name=self.collection_name,
                query=query_embedding,
                limit=limit,
                score_threshold=score_threshold,
                with_payload=True,
            )

            return [
                {**hit.payload, "similarity_score": hit.score}
                for hit in results.points
            ]

        except Exception as e:
            logger.error(f"[QDRANT] Search error: {e}")
            return []

    def delete_market(self, condition_id: str) -> bool:
        """Delete a market from the collection."""
        try:
            point_id = self._condition_id_to_point_id(condition_id)
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.PointIdsList(points=[point_id]),
            )
            return True
        except Exception as e:
            logger.error(f"[QDRANT] Delete error: {e}")
            return False

    def get_collection_info(self) -> dict:
        """Get collection statistics."""
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "name": self.collection_name,
                "points_count": info.points_count,
                "status": str(info.status),
            }
        except Exception as e:
            return {"error": str(e)}

    def clear_collection(self) -> bool:
        """Delete and recreate the collection."""
        try:
            self.client.delete_collection(self.collection_name)
            self._ensure_collection()
            return True
        except Exception as e:
            logger.error(f"[QDRANT] Clear collection error: {e}")
            return False

    def is_qdrant_configured(self) -> bool:
        """Check if Qdrant connection is configured."""
        return bool(self.qdrant_url)

    def is_configured(self) -> bool:
        """Check if Qdrant and OpenAI are configured (needed for embedding/search)."""
        return bool(self.qdrant_url and self.openai_api_key)
