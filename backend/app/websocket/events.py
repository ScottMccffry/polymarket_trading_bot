"""WebSocket event types and payloads."""
from enum import Enum
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class EventType(str, Enum):
    """WebSocket event types."""
    # Position events
    POSITIONS_BATCH = "positions_batch"      # Batch update after scheduler check
    POSITION_UPDATE = "position_update"      # Single position price/P&L changed
    POSITION_CLOSED = "position_closed"      # Position exited
    POSITION_OPENED = "position_opened"      # New position opened

    # Signal events
    SIGNAL_CREATED = "signal_created"        # New signal detected

    # Portfolio events
    PORTFOLIO_UPDATE = "portfolio_update"    # Overall stats changed

    # Analytics events
    ANALYTICS_UPDATE = "analytics_update"    # Analytics stats changed

    # System events
    HEARTBEAT = "heartbeat"                  # Keep-alive ping
    PONG = "pong"                            # Response to client ping
    ERROR = "error"                          # Error notification


class PositionUpdatePayload(BaseModel):
    """Payload for single position update."""
    position_id: int
    current_price: float
    unrealized_pnl: float
    unrealized_pnl_percent: float


class PositionsBatchPayload(BaseModel):
    """Payload for batch position updates."""
    positions: list[dict[str, Any]]


class PositionClosedPayload(BaseModel):
    """Payload when a position is closed."""
    position_id: int
    exit_price: float
    realized_pnl: float
    realized_pnl_percent: float
    reason: str


class PositionOpenedPayload(BaseModel):
    """Payload when a new position is opened."""
    position_id: int
    market_question: str | None
    side: str | None
    entry_price: float
    size: float
    strategy_name: str | None


class SignalCreatedPayload(BaseModel):
    """Payload when a new signal is detected."""
    signal_id: str
    source: str | None
    market_question: str | None
    side: str | None
    confidence: float | None
    created_at: str | None


class PortfolioUpdatePayload(BaseModel):
    """Payload for portfolio stats update."""
    unrealized_pnl: float
    realized_pnl: float | None = None
    open_positions_count: int
    total_value: float | None = None


class AnalyticsUpdatePayload(BaseModel):
    """Payload for analytics stats update."""
    total_realized_pnl: float
    total_unrealized_pnl: float
    total_trades: int
    open_trades: int
    win_rate: float
    max_drawdown: float
    profit_factor: float | None


class WebSocketEvent(BaseModel):
    """Standard WebSocket event wrapper."""
    type: EventType
    payload: dict[str, Any]
    timestamp: str

    @classmethod
    def create(cls, event_type: EventType, payload: dict[str, Any]) -> "WebSocketEvent":
        """Create a new WebSocket event with current timestamp."""
        return cls(
            type=event_type,
            payload=payload,
            timestamp=datetime.utcnow().isoformat()
        )
