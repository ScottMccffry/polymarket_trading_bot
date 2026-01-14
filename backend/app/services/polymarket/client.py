"""Polymarket API client."""
import httpx
from dataclasses import dataclass

from ...config import Settings, get_settings


@dataclass
class OrderBook:
    bids: list[dict]
    asks: list[dict]


class PolymarketClient:
    """Client for interacting with Polymarket APIs."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self.clob_url = self.settings.polymarket_clob_url
        self.gamma_url = self.settings.polymarket_gamma_url

    def get_markets(
        self,
        limit: int = 50,
        offset: int = 0,
        closed: str = "false",
        end_date_min: str | None = None,
    ) -> list[dict]:
        """Fetch markets from Gamma API."""
        params = {
            "limit": limit,
            "offset": offset,
            "closed": closed,
            "active": "true",
        }
        if end_date_min:
            params["end_date_min"] = end_date_min

        with httpx.Client(timeout=30) as client:
            resp = client.get(f"{self.gamma_url}/markets", params=params)
            resp.raise_for_status()
            return resp.json()

    def get_market(self, condition_id: str) -> dict | None:
        """Fetch a single market by condition ID."""
        with httpx.Client(timeout=10) as client:
            resp = client.get(f"{self.gamma_url}/markets/{condition_id}")
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            return resp.json()

    def get_orderbook(self, token_id: str) -> OrderBook:
        """Fetch orderbook for a token."""
        with httpx.Client(timeout=10) as client:
            resp = client.get(f"{self.clob_url}/book", params={"token_id": token_id})
            resp.raise_for_status()
            data = resp.json()
            return OrderBook(bids=data.get("bids", []), asks=data.get("asks", []))

    def get_price(self, token_id: str) -> dict:
        """Get current price for a token."""
        with httpx.Client(timeout=10) as client:
            resp = client.get(f"{self.clob_url}/price", params={"token_id": token_id})
            resp.raise_for_status()
            return resp.json()

    def get_midpoint(self, token_id: str) -> float | None:
        """Get midpoint price for a token."""
        with httpx.Client(timeout=10) as client:
            resp = client.get(f"{self.clob_url}/midpoint", params={"token_id": token_id})
            resp.raise_for_status()
            data = resp.json()
            return float(data.get("mid")) if data.get("mid") else None

    def get_price_history(
        self,
        token_id: str,
        interval: str = "1h",
        fidelity: int = 60,
    ) -> list[dict]:
        """
        Get price history for a token.

        Args:
            token_id: The token ID to get price history for
            interval: Time interval (e.g., '1h', '6h', '1d', '1w', 'max')
            fidelity: Number of data points (default 60)

        Returns:
            List of price history points with timestamp and price
        """
        with httpx.Client(timeout=30) as client:
            resp = client.get(
                f"{self.clob_url}/prices-history",
                params={
                    "market": token_id,
                    "interval": interval,
                    "fidelity": fidelity,
                }
            )
            resp.raise_for_status()
            data = resp.json()
            # API returns {"history": [{"t": timestamp, "p": price}, ...]}
            return data.get("history", [])
