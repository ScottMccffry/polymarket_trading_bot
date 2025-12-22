"""Event definitions for the event-driven architecture."""

from dataclasses import dataclass, field
from datetime import datetime, timezone


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class Event:
    """Base event class."""

    timestamp: datetime = field(default_factory=_utc_now)


@dataclass(frozen=True)
class MessageReceived(Event):
    """Fired when a Telegram message is received."""

    message_id: int = 0
    chat_id: int = 0
    chat_title: str = ""
    text: str = ""
    sender: str = ""


@dataclass(frozen=True)
class SignalCreated(Event):
    """Fired when a trading signal is created."""

    signal_id: str = ""
    market_id: str = ""
    market_question: str = ""
    side: str = ""
    confidence: float = 0.0
    price: float = 0.0
    source: str = ""


@dataclass(frozen=True)
class PositionOpened(Event):
    """Fired when a position is opened."""

    position_id: str = ""
    signal_id: str = ""
    market_id: str = ""
    strategy: str = ""
    side: str = ""
    entry_price: float = 0.0
    size: float = 0.0
    capital: float = 0.0


@dataclass(frozen=True)
class PriceUpdated(Event):
    """Fired when a position's price is updated."""

    position_id: str = ""
    price: float = 0.0
    pnl: float = 0.0
    pnl_percent: float = 0.0


@dataclass(frozen=True)
class PositionClosed(Event):
    """Fired when a position is closed."""

    position_id: str = ""
    exit_price: float = 0.0
    pnl: float = 0.0
    reason: str = ""


@dataclass(frozen=True)
class MarketDataUpdated(Event):
    """Fired when market orderbook data is updated."""

    market_id: str = ""
    token_id: str = ""
    bid: float = 0.0
    ask: float = 0.0
    spread: float = 0.0
