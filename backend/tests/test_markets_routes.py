"""Tests for markets API routes."""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, UTC, timedelta

from app.models.market import Market


class TestMarketsRoutes:
    """Test suite for markets API endpoints."""

    @pytest.mark.asyncio
    async def test_get_markets_empty(self, client):
        """Test getting markets when none exist."""
        response = await client.get("/api/markets")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_get_markets(self, client, db_session):
        """Test getting markets."""
        now = datetime.now(UTC).isoformat()
        market = Market(
            condition_id="0x123",
            question="Test market?",
            liquidity=1000,
            volume=5000,
            active=1,
            closed=0,
            created_at=now,
            updated_at=now,
        )
        db_session.add(market)
        await db_session.commit()

        response = await client.get("/api/markets")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["condition_id"] == "0x123"
        assert data[0]["question"] == "Test market?"

    @pytest.mark.asyncio
    async def test_get_markets_with_search(self, client, db_session):
        """Test searching markets by question."""
        now = datetime.now(UTC).isoformat()
        market1 = Market(
            condition_id="0x001",
            question="Will Bitcoin reach $100k?",
            volume=5000,
            active=1,
            closed=0,
            created_at=now,
            updated_at=now,
        )
        market2 = Market(
            condition_id="0x002",
            question="Will election be close?",
            volume=10000,
            active=1,
            closed=0,
            created_at=now,
            updated_at=now,
        )
        db_session.add_all([market1, market2])
        await db_session.commit()

        response = await client.get("/api/markets?search=Bitcoin")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["condition_id"] == "0x001"

    @pytest.mark.asyncio
    async def test_get_markets_with_category_filter(self, client, db_session):
        """Test filtering markets by category."""
        now = datetime.now(UTC).isoformat()
        market1 = Market(
            condition_id="0x001",
            question="Crypto market",
            category="Crypto",
            volume=5000,
            active=1,
            closed=0,
            created_at=now,
            updated_at=now,
        )
        market2 = Market(
            condition_id="0x002",
            question="Politics market",
            category="Politics",
            volume=10000,
            active=1,
            closed=0,
            created_at=now,
            updated_at=now,
        )
        db_session.add_all([market1, market2])
        await db_session.commit()

        response = await client.get("/api/markets?category=Crypto")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["category"] == "Crypto"

    @pytest.mark.asyncio
    async def test_get_markets_count(self, client, db_session):
        """Test getting market count."""
        now = datetime.now(UTC).isoformat()
        for i in range(5):
            market = Market(
                condition_id=f"0x{i:03d}",
                question=f"Market {i}",
                active=1,
                closed=0,
                created_at=now,
                updated_at=now,
            )
            db_session.add(market)
        await db_session.commit()

        response = await client.get("/api/markets/count")
        assert response.status_code == 200
        assert response.json()["count"] == 5

    @pytest.mark.asyncio
    async def test_get_categories(self, client, db_session):
        """Test getting unique categories."""
        now = datetime.now(UTC).isoformat()
        market1 = Market(
            condition_id="0x001",
            question="Crypto market",
            category="Crypto",
            active=1,
            closed=0,
            created_at=now,
            updated_at=now,
        )
        market2 = Market(
            condition_id="0x002",
            question="Politics market",
            category="Politics",
            active=1,
            closed=0,
            created_at=now,
            updated_at=now,
        )
        market3 = Market(
            condition_id="0x003",
            question="Another crypto market",
            category="Crypto",
            active=1,
            closed=0,
            created_at=now,
            updated_at=now,
        )
        db_session.add_all([market1, market2, market3])
        await db_session.commit()

        response = await client.get("/api/markets/categories")
        assert response.status_code == 200
        categories = response.json()["categories"]
        assert set(categories) == {"Crypto", "Politics"}

    @pytest.mark.asyncio
    async def test_get_single_market(self, client, db_session):
        """Test getting a single market by condition_id."""
        now = datetime.now(UTC).isoformat()
        market = Market(
            condition_id="0x123abc",
            question="Test market?",
            liquidity=1000,
            volume=5000,
            active=1,
            closed=0,
            created_at=now,
            updated_at=now,
        )
        db_session.add(market)
        await db_session.commit()

        response = await client.get("/api/markets/0x123abc")
        assert response.status_code == 200
        data = response.json()
        assert data["condition_id"] == "0x123abc"

    @pytest.mark.asyncio
    async def test_get_market_not_found(self, client):
        """Test getting non-existent market returns 404."""
        response = await client.get("/api/markets/nonexistent")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_market(self, client):
        """Test creating a new market."""
        market_data = {
            "condition_id": "0x123",
            "question": "New market?",
            "liquidity": 1000,
            "volume": 5000,
        }
        response = await client.post("/api/markets", json=market_data)
        assert response.status_code == 200
        data = response.json()
        assert data["condition_id"] == "0x123"
        assert data["question"] == "New market?"

    @pytest.mark.asyncio
    async def test_create_duplicate_market(self, client, db_session):
        """Test creating duplicate market returns error."""
        now = datetime.now(UTC).isoformat()
        market = Market(
            condition_id="0x123",
            question="Existing market",
            active=1,
            closed=0,
            created_at=now,
            updated_at=now,
        )
        db_session.add(market)
        await db_session.commit()

        market_data = {
            "condition_id": "0x123",
            "question": "Duplicate market",
        }
        response = await client.post("/api/markets", json=market_data)
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_update_market(self, client, db_session):
        """Test updating a market."""
        now = datetime.now(UTC).isoformat()
        market = Market(
            condition_id="0x123",
            question="Original question",
            volume=1000,
            active=1,
            closed=0,
            created_at=now,
            updated_at=now,
        )
        db_session.add(market)
        await db_session.commit()

        update_data = {"question": "Updated question", "volume": 5000}
        response = await client.put("/api/markets/0x123", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["question"] == "Updated question"
        assert data["volume"] == 5000

    @pytest.mark.asyncio
    async def test_delete_market(self, client, db_session):
        """Test deleting a market."""
        now = datetime.now(UTC).isoformat()
        market = Market(
            condition_id="0x123",
            question="To be deleted",
            active=1,
            closed=0,
            created_at=now,
            updated_at=now,
        )
        db_session.add(market)
        await db_session.commit()

        response = await client.delete("/api/markets/0x123")
        assert response.status_code == 200
        assert "deleted" in response.json()["message"].lower()

        # Verify deletion
        response = await client.get("/api/markets/0x123")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_all_markets_requires_confirm(self, client):
        """Test delete all markets requires confirmation."""
        response = await client.delete("/api/markets")
        assert response.status_code == 400
        assert "confirm=true" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_delete_all_markets(self, client, db_session):
        """Test deleting all markets with confirmation."""
        now = datetime.now(UTC).isoformat()
        for i in range(3):
            market = Market(
                condition_id=f"0x{i:03d}",
                question=f"Market {i}",
                active=1,
                closed=0,
                created_at=now,
                updated_at=now,
            )
            db_session.add(market)
        await db_session.commit()

        response = await client.delete("/api/markets?confirm=true")
        assert response.status_code == 200
        assert "3 markets" in response.json()["message"]

        # Verify all deleted
        response = await client.get("/api/markets")
        assert response.json() == []

    @patch("app.routes.markets.MarketHarvester")
    @pytest.mark.asyncio
    async def test_harvest_markets(self, mock_harvester_class, client):
        """Test harvest endpoint."""
        mock_harvester = MagicMock()
        mock_harvester.harvest = MagicMock(return_value=100)
        mock_harvester_class.return_value = mock_harvester

        # Make harvest async
        async def mock_harvest(*args, **kwargs):
            return 100
        mock_harvester.harvest = mock_harvest

        response = await client.post("/api/markets/harvest?max_markets=100")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 100

    @patch("app.routes.markets.PolymarketClient")
    @pytest.mark.asyncio
    async def test_get_token_price(self, mock_client_class, client):
        """Test get price endpoint."""
        mock_client = MagicMock()
        mock_client.get_price.return_value = {"price": "0.55"}
        mock_client_class.return_value = mock_client

        response = await client.get("/api/markets/price/token123")
        assert response.status_code == 200
        assert response.json()["price"] == "0.55"

    @patch("app.routes.markets.PolymarketClient")
    @pytest.mark.asyncio
    async def test_get_token_orderbook(self, mock_client_class, client):
        """Test get orderbook endpoint."""
        mock_client = MagicMock()
        mock_orderbook = MagicMock()
        mock_orderbook.bids = [{"price": "0.55", "size": "100"}]
        mock_orderbook.asks = [{"price": "0.56", "size": "200"}]
        mock_client.get_orderbook.return_value = mock_orderbook
        mock_client_class.return_value = mock_client

        response = await client.get("/api/markets/orderbook/token123")
        assert response.status_code == 200
        data = response.json()
        assert len(data["bids"]) == 1
        assert len(data["asks"]) == 1

    @pytest.mark.asyncio
    async def test_search_markets_endpoint(self, client, db_session):
        """Test search markets endpoint."""
        now = datetime.now(UTC).isoformat()
        future_date = (datetime.now(UTC) + timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")

        market = Market(
            condition_id="0x001",
            question="Will Bitcoin reach $100k?",
            active=1,
            closed=0,
            end_date_iso=future_date,
            volume=5000,
            created_at=now,
            updated_at=now,
        )
        db_session.add(market)
        await db_session.commit()

        response = await client.get("/api/markets/search?q=Bitcoin")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert "Bitcoin" in data[0]["question"]

    @pytest.mark.asyncio
    async def test_search_markets_no_keywords(self, client):
        """Test search with no keywords returns error."""
        response = await client.get("/api/markets/search?q=")
        assert response.status_code == 400
