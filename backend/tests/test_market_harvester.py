"""Tests for MarketHarvester."""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, UTC, timedelta

from sqlalchemy import select

from app.services.polymarket.markets import MarketHarvester
from app.models.market import Market


class TestMarketHarvester:
    """Test suite for MarketHarvester."""

    def test_harvester_initialization(self):
        """Test harvester initializes correctly."""
        harvester = MarketHarvester()
        assert harvester.client is not None
        assert harvester.settings is not None

    @patch.object(MarketHarvester, "fetch_markets")
    @pytest.mark.asyncio
    async def test_harvest_stores_markets(self, mock_fetch, db_session, sample_market_data):
        """Test harvesting stores markets in database."""
        mock_fetch.return_value = [sample_market_data]

        harvester = MarketHarvester()
        count = await harvester.harvest(db_session, max_markets=10)

        assert count == 1

        # Verify market was stored
        result = await db_session.execute(
            select(Market).where(Market.condition_id == "0x123abc")
        )
        market = result.scalar_one_or_none()
        assert market is not None
        assert market.question == "Will Bitcoin reach $100k by end of 2025?"
        assert market.liquidity == 50000.0
        assert market.category == "Crypto"

    @patch.object(MarketHarvester, "fetch_markets")
    @pytest.mark.asyncio
    async def test_harvest_updates_existing_market(self, mock_fetch, db_session, sample_market_data):
        """Test harvesting updates existing markets."""
        # First harvest
        mock_fetch.return_value = [sample_market_data]
        harvester = MarketHarvester()
        await harvester.harvest(db_session, max_markets=10)

        # Update market data
        updated_data = sample_market_data.copy()
        updated_data["volume"] = 200000.0
        mock_fetch.return_value = [updated_data]

        # Second harvest
        count = await harvester.harvest(db_session, max_markets=10)
        assert count == 1

        # Verify market was updated
        result = await db_session.execute(
            select(Market).where(Market.condition_id == "0x123abc")
        )
        market = result.scalar_one_or_none()
        assert market.volume == 200000.0

    @patch.object(MarketHarvester, "fetch_markets")
    @pytest.mark.asyncio
    async def test_harvest_skips_invalid_markets(self, mock_fetch, db_session):
        """Test harvesting skips markets without condition_id."""
        mock_fetch.return_value = [
            {"question": "Invalid market without ID"},  # No conditionId
        ]

        harvester = MarketHarvester()
        count = await harvester.harvest(db_session, max_markets=10)

        assert count == 0

    @patch.object(MarketHarvester, "fetch_markets")
    @pytest.mark.asyncio
    async def test_harvest_handles_json_token_ids(self, mock_fetch, db_session, sample_market_data):
        """Test harvesting handles JSON string token IDs."""
        # Some APIs return token IDs as JSON string
        market_data = sample_market_data.copy()
        market_data["clobTokenIds"] = '["token1", "token2"]'
        mock_fetch.return_value = [market_data]

        harvester = MarketHarvester()
        await harvester.harvest(db_session, max_markets=10)

        result = await db_session.execute(
            select(Market).where(Market.condition_id == "0x123abc")
        )
        market = result.scalar_one_or_none()
        assert market is not None
        assert market.clob_token_ids == '["token1", "token2"]'

    @pytest.mark.asyncio
    async def test_search_by_keywords(self, db_session):
        """Test searching markets by keywords."""
        # Create test markets
        now = datetime.now(UTC).isoformat()
        future_date = (datetime.now(UTC) + timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")

        market1 = Market(
            condition_id="0x001",
            question="Will Bitcoin reach $100k?",
            active=1,
            closed=0,
            end_date_iso=future_date,
            liquidity=1000,
            volume=5000,
            created_at=now,
            updated_at=now,
        )
        market2 = Market(
            condition_id="0x002",
            question="Will Ethereum flip Bitcoin?",
            active=1,
            closed=0,
            end_date_iso=future_date,
            liquidity=2000,
            volume=10000,
            created_at=now,
            updated_at=now,
        )
        market3 = Market(
            condition_id="0x003",
            question="Will the election be close?",
            active=1,
            closed=0,
            end_date_iso=future_date,
            liquidity=3000,
            volume=15000,
            created_at=now,
            updated_at=now,
        )
        db_session.add_all([market1, market2, market3])
        await db_session.commit()

        harvester = MarketHarvester()
        results = await harvester.search(db_session, keywords=["Bitcoin"], limit=10)

        assert len(results) == 2
        # Results should be ordered by volume (descending)
        assert results[0].condition_id == "0x002"  # Higher volume
        assert results[1].condition_id == "0x001"

    @pytest.mark.asyncio
    async def test_search_excludes_closed_markets(self, db_session):
        """Test search excludes closed markets."""
        now = datetime.now(UTC).isoformat()
        future_date = (datetime.now(UTC) + timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")

        market1 = Market(
            condition_id="0x001",
            question="Will Bitcoin reach $100k?",
            active=1,
            closed=1,  # Closed
            end_date_iso=future_date,
            liquidity=1000,
            volume=5000,
            created_at=now,
            updated_at=now,
        )
        db_session.add(market1)
        await db_session.commit()

        harvester = MarketHarvester()
        results = await harvester.search(db_session, keywords=["Bitcoin"], limit=10)

        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_search_excludes_expired_markets(self, db_session):
        """Test search excludes markets ending soon."""
        now = datetime.now(UTC).isoformat()
        # Market ending tomorrow (within min_days_until_end)
        tomorrow = (datetime.now(UTC) + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")

        market1 = Market(
            condition_id="0x001",
            question="Will Bitcoin reach $100k?",
            active=1,
            closed=0,
            end_date_iso=tomorrow,  # Ending too soon
            liquidity=1000,
            volume=5000,
            created_at=now,
            updated_at=now,
        )
        db_session.add(market1)
        await db_session.commit()

        harvester = MarketHarvester()
        results = await harvester.search(db_session, keywords=["Bitcoin"], limit=10)

        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_search_empty_keywords(self, db_session):
        """Test search with empty keywords returns empty list."""
        harvester = MarketHarvester()
        results = await harvester.search(db_session, keywords=[], limit=10)
        assert results == []

    @pytest.mark.asyncio
    async def test_count_active(self, db_session):
        """Test counting active markets."""
        now = datetime.now(UTC).isoformat()

        market1 = Market(
            condition_id="0x001",
            question="Market 1",
            active=1,
            closed=0,
            created_at=now,
            updated_at=now,
        )
        market2 = Market(
            condition_id="0x002",
            question="Market 2",
            active=1,
            closed=0,
            created_at=now,
            updated_at=now,
        )
        market3 = Market(
            condition_id="0x003",
            question="Market 3",
            active=0,  # Inactive
            closed=0,
            created_at=now,
            updated_at=now,
        )
        db_session.add_all([market1, market2, market3])
        await db_session.commit()

        harvester = MarketHarvester()
        count = await harvester.count_active(db_session)

        assert count == 2

    @patch("app.services.polymarket.markets.PolymarketClient.get_markets")
    def test_fetch_markets_pagination(self, mock_get_markets):
        """Test fetch_markets handles pagination."""
        # First call returns 50 markets, second returns 25, third returns empty
        mock_get_markets.side_effect = [
            [{"conditionId": f"0x{i}"} for i in range(50)],
            [{"conditionId": f"0x{i}"} for i in range(50, 75)],
            [],
        ]

        harvester = MarketHarvester()
        markets = harvester.fetch_markets(max_markets=100)

        assert len(markets) == 75
        assert mock_get_markets.call_count == 3
