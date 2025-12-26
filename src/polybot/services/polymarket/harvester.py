"""Market harvester for fetching and storing Polymarket markets."""

from datetime import datetime, timezone, timedelta
from typing import Any
import structlog

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from .client import PolymarketClient
from ...config import get_settings
from ...models.market import Market
from ...db.session import get_session

logger = structlog.get_logger()


class MarketHarvester:
    """Fetches markets from Polymarket and stores them in the database."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.client = PolymarketClient()

    async def harvest(
        self,
        max_markets: int = 5000,
        batch_size: int = 100,
    ) -> int:
        """Fetch and store markets from Polymarket.

        Returns:
            Number of markets processed
        """
        logger.info("harvest_started", max_markets=max_markets)

        total_processed = 0
        offset = 0

        try:
            while total_processed < max_markets:
                # Fetch batch from API
                markets_data = await self.client.get_markets(
                    limit=batch_size,
                    offset=offset,
                    active=True,
                )

                if not markets_data:
                    break

                # Filter and store
                valid_markets = self._filter_markets(markets_data)

                if valid_markets:
                    async with get_session() as session:
                        await self._upsert_markets(session, valid_markets)

                total_processed += len(markets_data)
                offset += batch_size

                logger.debug(
                    "harvest_batch",
                    processed=total_processed,
                    valid=len(valid_markets),
                )

        finally:
            await self.client.close()

        logger.info("harvest_completed", total_markets=total_processed)
        return total_processed

    def _filter_markets(self, markets_data: list[dict[str, Any]]) -> list[Market]:
        """Filter markets based on criteria."""
        valid = []
        now = datetime.now(timezone.utc)
        min_end_date = now + timedelta(days=self.settings.min_days_until_end)

        for data in markets_data:
            # Skip if no token IDs
            token_ids = data.get("clobTokenIds", [])
            if not token_ids or len(token_ids) < 2:
                continue

            # Parse end date
            end_date_str = data.get("endDate") or data.get("endDateIso")
            if end_date_str:
                try:
                    end_date = datetime.fromisoformat(
                        end_date_str.replace("Z", "+00:00")
                    )
                    # Skip if ending too soon
                    if end_date < min_end_date:
                        continue
                except ValueError:
                    end_date = None
            else:
                end_date = None

            # Create market object
            market = Market(
                condition_id=data["conditionId"],
                question=data.get("question", ""),
                description=data.get("description"),
                slug=data.get("slug"),
                category=data.get("category"),
                clob_token_ids=token_ids,
                liquidity=float(data.get("liquidity", 0) or 0),
                volume=float(data.get("volume", 0) or 0),
                end_date=end_date,
                active=data.get("active", True),
                closed=data.get("closed", False),
            )
            valid.append(market)

        return valid

    async def _upsert_markets(
        self,
        session: AsyncSession,
        markets: list[Market],
    ) -> None:
        """Upsert markets into database."""
        for market in markets:
            # SQLite upsert
            stmt = sqlite_insert(Market).values(
                condition_id=market.condition_id,
                question=market.question,
                description=market.description,
                slug=market.slug,
                category=market.category,
                clob_token_ids=market.clob_token_ids,
                liquidity=market.liquidity,
                volume=market.volume,
                end_date=market.end_date,
                active=market.active,
                closed=market.closed,
                updated_at=datetime.now(timezone.utc),
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["condition_id"],
                set_={
                    "question": stmt.excluded.question,
                    "description": stmt.excluded.description,
                    "liquidity": stmt.excluded.liquidity,
                    "volume": stmt.excluded.volume,
                    "active": stmt.excluded.active,
                    "closed": stmt.excluded.closed,
                    "updated_at": stmt.excluded.updated_at,
                },
            )
            await session.execute(stmt)
