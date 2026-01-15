"""Market harvesting service."""
import json
import logging
from datetime import datetime, UTC, timedelta

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ...config import Settings, get_settings
from ...models.market import Market
from .client import PolymarketClient

logger = logging.getLogger(__name__)


class MarketHarvester:
    """Service for harvesting markets from Polymarket API and storing in database."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self.client = PolymarketClient(self.settings)
        self._qdrant = None

    @property
    def qdrant(self):
        """Lazy-initialize Qdrant service if configured."""
        if self._qdrant is None:
            from ..qdrant import QdrantService
            try:
                service = QdrantService(self.settings)
                if service.is_configured():
                    self._qdrant = service
                    logger.info("[HARVESTER] Qdrant service initialized")
            except Exception as e:
                logger.debug(f"[HARVESTER] Qdrant not available: {e}")
        return self._qdrant

    def fetch_markets(self, max_markets: int = 5000) -> list[dict]:
        """Fetch markets from Polymarket API."""
        all_markets = []
        offset = 0
        limit = 50

        min_end = datetime.now(UTC) + timedelta(days=self.settings.min_days_until_end)
        end_date_min = min_end.strftime("%Y-%m-%dT00:00:00Z")

        while len(all_markets) < max_markets:
            batch = self.client.get_markets(
                limit=limit, offset=offset, end_date_min=end_date_min
            )
            if not batch:
                break
            all_markets.extend(batch)
            offset += limit

        return all_markets

    async def harvest(self, db: AsyncSession, max_markets: int = 5000) -> int:
        """Fetch and store markets from Polymarket API."""
        all_markets = self.fetch_markets(max_markets)

        stored = 0
        now = datetime.now(UTC).isoformat()

        for m in all_markets:
            # API returns conditionId (camelCase)
            condition_id = m.get("conditionId") or m.get("condition_id")
            if not condition_id:
                continue

            token_ids = m.get("clobTokenIds", [])
            # API may return clobTokenIds as a JSON string or a list
            if isinstance(token_ids, str):
                token_ids_str = token_ids if token_ids else None
            else:
                token_ids_str = json.dumps(token_ids) if token_ids else None

            # Check if market exists
            result = await db.execute(
                select(Market).where(Market.condition_id == condition_id)
            )
            existing = result.scalar_one_or_none()

            # Parse liquidity and volume as floats (API may return strings)
            liquidity = float(m.get("liquidity") or 0)
            volume = float(m.get("volume") or 0)

            if existing:
                # Update existing market
                existing.question = m.get("question")
                existing.description = m.get("description")
                existing.market_slug = m.get("slug")
                existing.end_date_iso = m.get("endDate")
                existing.clob_token_ids = token_ids_str
                existing.liquidity = liquidity
                existing.volume = volume
                existing.category = m.get("category")
                existing.active = 1 if m.get("active", True) else 0
                existing.closed = 1 if m.get("closed", False) else 0
                existing.updated_at = now
            else:
                # Create new market
                market = Market(
                    condition_id=condition_id,
                    question=m.get("question"),
                    description=m.get("description"),
                    market_slug=m.get("slug"),
                    end_date_iso=m.get("endDate"),
                    clob_token_ids=token_ids_str,
                    liquidity=liquidity,
                    volume=volume,
                    category=m.get("category"),
                    active=1 if m.get("active", True) else 0,
                    closed=1 if m.get("closed", False) else 0,
                    created_at=now,
                    updated_at=now,
                )
                db.add(market)

            stored += 1

        await db.commit()

        # Embed in Qdrant if configured
        if self.qdrant and all_markets:
            logger.info(f"[HARVESTER] Embedding {len(all_markets)} markets in Qdrant...")
            qdrant_stored = self.qdrant.upsert_markets_batch(all_markets)
            logger.info(f"[HARVESTER] Embedded {qdrant_stored} markets in Qdrant")

        return stored

    async def search(
        self,
        db: AsyncSession,
        keywords: list[str],
        limit: int = 100,
    ) -> list[Market]:
        """Search markets by keywords."""
        if not keywords:
            return []

        min_end = datetime.now(UTC) + timedelta(days=self.settings.min_days_until_end)
        min_end_str = min_end.strftime("%Y-%m-%dT%H:%M:%SZ")

        query = select(Market).where(
            Market.active == 1,
            Market.closed == 0,
            Market.end_date_iso > min_end_str,
        )

        # Add keyword filters (OR condition)
        keyword_conditions = [Market.question.ilike(f"%{kw}%") for kw in keywords]
        from sqlalchemy import or_
        query = query.where(or_(*keyword_conditions))

        query = query.order_by(Market.volume.desc()).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def count_active(self, db: AsyncSession) -> int:
        """Count active markets in database."""
        result = await db.execute(
            select(func.count()).select_from(Market).where(
                Market.active == 1,
                Market.closed == 0,
            )
        )
        return result.scalar() or 0
