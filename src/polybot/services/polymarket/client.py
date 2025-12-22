"""Polymarket REST API client."""

from typing import Any
import httpx
import structlog

from ...config import get_settings
from ...core.exceptions import PriceFetchError

logger = structlog.get_logger()


class PolymarketClient:
    """Client for Polymarket Gamma and CLOB APIs."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=30.0,
                limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
                headers={"User-Agent": "PolyBot/0.1.0"},
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    # Gamma API (public market data)

    async def get_markets(
        self,
        limit: int = 100,
        offset: int = 0,
        active: bool = True,
        closed: bool = False,
    ) -> list[dict[str, Any]]:
        """Fetch markets from Gamma API."""
        client = await self._get_client()

        params = {
            "limit": limit,
            "offset": offset,
            "active": str(active).lower(),
            "closed": str(closed).lower(),
        }

        try:
            response = await client.get(
                f"{self.settings.polymarket_gamma_url}/markets",
                params=params,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error("gamma_api_error", error=str(e), params=params)
            raise

    async def get_market(self, condition_id: str) -> dict[str, Any] | None:
        """Fetch a single market by condition_id."""
        client = await self._get_client()

        try:
            response = await client.get(
                f"{self.settings.polymarket_gamma_url}/markets/{condition_id}"
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error("gamma_api_error", error=str(e), condition_id=condition_id)
            raise

    # CLOB API (orderbook data)

    async def get_orderbook(self, token_id: str) -> dict[str, Any]:
        """Fetch orderbook from CLOB API."""
        client = await self._get_client()

        try:
            response = await client.get(
                f"{self.settings.polymarket_clob_url}/book",
                params={"token_id": token_id},
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error("clob_api_error", error=str(e), token_id=token_id)
            raise PriceFetchError(f"Failed to fetch orderbook: {e}")

    async def get_best_prices(self, token_id: str) -> tuple[float, float]:
        """Get best bid and ask prices for a token.

        Returns:
            Tuple of (best_bid, best_ask)
        """
        book = await self.get_orderbook(token_id)

        bids = book.get("bids", [])
        asks = book.get("asks", [])

        best_bid = float(bids[0]["price"]) if bids else 0.0
        best_ask = float(asks[0]["price"]) if asks else 1.0

        return best_bid, best_ask

    async def get_mid_price(self, token_id: str) -> float:
        """Get mid price for a token."""
        bid, ask = await self.get_best_prices(token_id)
        return (bid + ask) / 2

    async def get_spread(self, token_id: str) -> float:
        """Get spread as a percentage."""
        bid, ask = await self.get_best_prices(token_id)
        if ask == 0:
            return 100.0
        return ((ask - bid) / ask) * 100

    async def get_price(self, token_id: str) -> float:
        """Get the current price (best ask) for a token."""
        _, ask = await self.get_best_prices(token_id)
        return ask
