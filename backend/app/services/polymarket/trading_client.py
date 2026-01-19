"""
Polymarket CLOB Trading Client

Wraps py-clob-client for real order execution with safety controls.
Uses lazy initialization pattern consistent with other services.
"""

import logging
import json
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
from enum import Enum

from py_clob_client.client import ClobClient
from py_clob_client.clob_types import OrderArgs, OrderType, BalanceAllowanceParams, AssetType
from py_clob_client.order_builder.constants import BUY, SELL

from ...config import Settings, get_settings

logger = logging.getLogger(__name__)

SETTINGS_FILE = Path("data/settings.json")


class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class TradingOrderType(str, Enum):
    GTC = "GTC"  # Good till cancelled
    FOK = "FOK"  # Fill or kill


@dataclass
class OrderResult:
    """Result of an order operation."""
    success: bool
    order_id: Optional[str] = None
    status: Optional[str] = None
    error: Optional[str] = None
    filled_size: float = 0.0
    average_price: Optional[float] = None


def _load_saved_settings() -> dict:
    """Load settings from JSON file."""
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def _save_settings(settings: dict) -> None:
    """Save settings to JSON file."""
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)


def _get_effective_setting(key: str, env_settings: Settings, saved: dict):
    """Get effective setting value, preferring saved over env."""
    if key in saved and saved[key]:
        return saved[key]
    return getattr(env_settings, key, None)


class ClobTradingClient:
    """
    Trading client for Polymarket CLOB.

    Uses lazy initialization pattern consistent with other services.
    Includes safety controls and validation.
    """

    def __init__(self, settings: Settings | None = None):
        self.env_settings = settings or get_settings()
        self._saved_settings = _load_saved_settings()

        # Get effective settings (saved > env)
        self.clob_url = self.env_settings.polymarket_clob_url
        self.private_key = _get_effective_setting(
            "polymarket_private_key", self.env_settings, self._saved_settings
        ) or ""
        self.funder_address = _get_effective_setting(
            "polymarket_funder_address", self.env_settings, self._saved_settings
        ) or ""
        self.chain_id = _get_effective_setting(
            "polymarket_chain_id", self.env_settings, self._saved_settings
        ) or 137
        self.signature_type = _get_effective_setting(
            "polymarket_signature_type", self.env_settings, self._saved_settings
        ) or 0

        # Safety settings
        self.live_trading_enabled = self._saved_settings.get(
            "live_trading_enabled",
            getattr(self.env_settings, "live_trading_enabled", False)
        )
        self.max_position_size = _get_effective_setting(
            "max_position_size", self.env_settings, self._saved_settings
        ) or 100.0
        self.max_open_positions = _get_effective_setting(
            "max_open_positions", self.env_settings, self._saved_settings
        ) or 10

        self._client: Optional[ClobClient] = None
        self._api_creds_set = False

    @property
    def client(self) -> ClobClient:
        """Lazy-initialize CLOB client with API credentials."""
        if self._client is None:
            if not self.is_configured():
                raise ValueError(
                    "Trading client not configured. "
                    "Set private key and funder address in settings."
                )

            self._client = ClobClient(
                self.clob_url,
                key=self.private_key,
                chain_id=self.chain_id,
                signature_type=self.signature_type,
                funder=self.funder_address,
            )

        if not self._api_creds_set:
            # Create or derive API credentials (required for trading)
            self._client.set_api_creds(self._client.create_or_derive_api_creds())
            self._api_creds_set = True
            logger.info("[TRADING] API credentials initialized")

        return self._client

    def is_configured(self) -> bool:
        """Check if trading is configured (has credentials)."""
        return bool(self.private_key and self.funder_address)

    def is_live_enabled(self) -> bool:
        """Check if live trading is enabled."""
        return self.is_configured() and self.live_trading_enabled

    def reload_settings(self) -> None:
        """Reload settings from file (after settings update)."""
        self._saved_settings = _load_saved_settings()
        self.live_trading_enabled = self._saved_settings.get("live_trading_enabled", False)
        self.max_position_size = self._saved_settings.get("max_position_size", 100.0)
        self.max_open_positions = self._saved_settings.get("max_open_positions", 10)
        self.private_key = self._saved_settings.get("polymarket_private_key", "") or self.env_settings.polymarket_private_key
        self.funder_address = self._saved_settings.get("polymarket_funder_address", "") or self.env_settings.polymarket_funder_address
        # Reset client to pick up new credentials if changed
        self._client = None
        self._api_creds_set = False
        logger.info("[TRADING] Settings reloaded")

    def validate_order(
        self,
        size_usd: float,
        current_open_positions: int
    ) -> tuple[bool, str]:
        """
        Validate order against safety limits.

        Returns: (is_valid, error_message)
        """
        if not self.is_live_enabled():
            return False, "Live trading is not enabled"

        if size_usd > self.max_position_size:
            return False, f"Order size ${size_usd:.2f} exceeds max ${self.max_position_size:.2f}"

        if current_open_positions >= self.max_open_positions:
            return False, f"Max open positions ({self.max_open_positions}) reached"

        return True, ""

    def place_market_order(
        self,
        token_id: str,
        side: OrderSide,
        size_usd: float,
        price: float,
    ) -> OrderResult:
        """
        Place a market order on Polymarket.

        Args:
            token_id: The token ID to trade
            side: BUY or SELL
            size_usd: Position size in USD
            price: Current market price (for share calculation)

        Returns:
            OrderResult with success status and order details
        """
        if not self.is_live_enabled():
            return OrderResult(
                success=False,
                error="Live trading is disabled"
            )

        if not token_id:
            return OrderResult(
                success=False,
                error="Token ID is required for trading"
            )

        try:
            # Calculate shares from USD size
            shares = size_usd / price if price > 0 else 0
            if shares <= 0:
                return OrderResult(success=False, error="Invalid share calculation")

            # Convert side to py-clob-client constant
            clob_side = BUY if side == OrderSide.BUY else SELL

            # Create the order
            order = self.client.create_order(OrderArgs(
                token_id=token_id,
                price=price,
                size=shares,
                side=clob_side,
            ))

            # Post as FOK (Fill or Kill) for market-like execution
            resp = self.client.post_order(order, OrderType.FOK)

            logger.info(
                f"[TRADING] Order placed: {side.value} ${size_usd:.2f} "
                f"({shares:.2f} shares) @ {price:.4f}"
            )
            logger.debug(f"[TRADING] Order response: {resp}")

            # Parse response
            order_id = resp.get("orderID") or resp.get("order_id") or resp.get("id")
            status = resp.get("status", "pending")

            return OrderResult(
                success=True,
                order_id=order_id,
                status=status,
            )

        except Exception as e:
            logger.error(f"[TRADING] Order failed: {e}")
            return OrderResult(
                success=False,
                error=str(e),
            )

    def cancel_order(self, order_id: str) -> OrderResult:
        """Cancel an open order."""
        if not self.is_live_enabled():
            return OrderResult(success=False, error="Live trading is disabled")

        try:
            resp = self.client.cancel(order_id)
            logger.info(f"[TRADING] Order cancelled: {order_id}")
            return OrderResult(success=True, order_id=order_id, status="cancelled")
        except Exception as e:
            logger.error(f"[TRADING] Cancel failed: {e}")
            return OrderResult(success=False, error=str(e))

    def cancel_all_orders(self) -> OrderResult:
        """Cancel all open orders."""
        if not self.is_live_enabled():
            return OrderResult(success=False, error="Live trading is disabled")

        try:
            resp = self.client.cancel_all()
            logger.info("[TRADING] All orders cancelled")
            return OrderResult(success=True, status="all_cancelled")
        except Exception as e:
            logger.error(f"[TRADING] Cancel all failed: {e}")
            return OrderResult(success=False, error=str(e))

    def get_order_status(self, order_id: str) -> OrderResult:
        """Get current status of an order."""
        try:
            resp = self.client.get_order(order_id)
            return OrderResult(
                success=True,
                order_id=order_id,
                status=resp.get("status"),
                filled_size=float(resp.get("size_matched", 0)),
                average_price=float(resp.get("price")) if resp.get("price") else None,
            )
        except Exception as e:
            logger.error(f"[TRADING] Get order status failed: {e}")
            return OrderResult(success=False, error=str(e))

    def get_open_orders(self, market: str | None = None) -> list[dict]:
        """Get all open orders, optionally filtered by market."""
        try:
            orders = self.client.get_orders()
            if market:
                orders = [o for o in orders if o.get("market") == market]
            return orders
        except Exception as e:
            logger.error(f"[TRADING] Get open orders failed: {e}")
            return []

    def get_balances(self) -> dict:
        """Get wallet balances (USDC, collateral)."""
        try:
            # Get USDC (collateral) balance
            usdc_params = BalanceAllowanceParams(
                asset_type=AssetType.COLLATERAL,
                signature_type=self.signature_type or 0
            )
            usdc_result = self.client.get_balance_allowance(usdc_params)

            return {
                "USDC": usdc_result.get("balance", "0"),
                "allowances": usdc_result.get("allowances", {})
            }
        except Exception as e:
            logger.error(f"[TRADING] Get balances failed: {e}")
            return {"error": str(e)}


# Singleton instance
trading_client = ClobTradingClient()
