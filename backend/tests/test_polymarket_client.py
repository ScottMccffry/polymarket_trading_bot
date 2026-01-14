"""Tests for PolymarketClient."""
import pytest
from unittest.mock import patch, MagicMock
import httpx

from app.services.polymarket.client import PolymarketClient, OrderBook


class TestPolymarketClient:
    """Test suite for PolymarketClient."""

    def test_client_initialization(self):
        """Test client initializes with correct URLs."""
        client = PolymarketClient()
        assert client.clob_url == "https://clob.polymarket.com"
        assert client.gamma_url == "https://gamma-api.polymarket.com"

    @patch("app.services.polymarket.client.httpx.Client")
    def test_get_markets(self, mock_client_class, sample_market_data):
        """Test fetching markets from Gamma API."""
        mock_response = MagicMock()
        mock_response.json.return_value = [sample_market_data]
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        client = PolymarketClient()
        markets = client.get_markets(limit=10, offset=0)

        assert len(markets) == 1
        assert markets[0]["conditionId"] == "0x123abc"
        assert markets[0]["question"] == "Will Bitcoin reach $100k by end of 2025?"
        mock_client.get.assert_called_once()

    @patch("app.services.polymarket.client.httpx.Client")
    def test_get_markets_with_filters(self, mock_client_class):
        """Test fetching markets with date filter."""
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        client = PolymarketClient()
        client.get_markets(
            limit=50,
            offset=100,
            closed="false",
            end_date_min="2025-01-01T00:00:00Z"
        )

        call_args = mock_client.get.call_args
        params = call_args.kwargs.get("params", {})
        assert params["limit"] == 50
        assert params["offset"] == 100
        assert params["end_date_min"] == "2025-01-01T00:00:00Z"

    @patch("app.services.polymarket.client.httpx.Client")
    def test_get_orderbook(self, mock_client_class, sample_orderbook_data):
        """Test fetching orderbook for a token."""
        mock_response = MagicMock()
        mock_response.json.return_value = sample_orderbook_data
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        client = PolymarketClient()
        orderbook = client.get_orderbook("token123")

        assert isinstance(orderbook, OrderBook)
        assert len(orderbook.bids) == 2
        assert len(orderbook.asks) == 2
        assert orderbook.bids[0]["price"] == "0.55"

    @patch("app.services.polymarket.client.httpx.Client")
    def test_get_price(self, mock_client_class, sample_price_data):
        """Test fetching price for a token."""
        mock_response = MagicMock()
        mock_response.json.return_value = sample_price_data
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        client = PolymarketClient()
        price = client.get_price("token123")

        assert price["price"] == "0.55"
        assert price["spread"] == "0.01"

    @patch("app.services.polymarket.client.httpx.Client")
    def test_get_midpoint(self, mock_client_class):
        """Test fetching midpoint price."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"mid": "0.555"}
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        client = PolymarketClient()
        midpoint = client.get_midpoint("token123")

        assert midpoint == 0.555

    @patch("app.services.polymarket.client.httpx.Client")
    def test_get_market_single(self, mock_client_class, sample_market_data):
        """Test fetching a single market."""
        mock_response = MagicMock()
        mock_response.json.return_value = sample_market_data
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        client = PolymarketClient()
        market = client.get_market("0x123abc")

        assert market["conditionId"] == "0x123abc"

    @patch("app.services.polymarket.client.httpx.Client")
    def test_get_market_not_found(self, mock_client_class):
        """Test fetching a non-existent market returns None."""
        mock_response = MagicMock()
        mock_response.status_code = 404

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        client = PolymarketClient()
        market = client.get_market("nonexistent")

        assert market is None

    @patch("app.services.polymarket.client.httpx.Client")
    def test_api_error_handling(self, mock_client_class):
        """Test API error is propagated."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Server error",
            request=MagicMock(),
            response=MagicMock(status_code=500)
        )

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        client = PolymarketClient()
        with pytest.raises(httpx.HTTPStatusError):
            client.get_markets()
