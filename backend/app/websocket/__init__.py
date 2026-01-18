"""WebSocket module for real-time updates."""
from .manager import manager
from .router import router as websocket_router
from .events import (
    EventType,
    WebSocketEvent,
    PositionUpdatePayload,
    PositionsBatchPayload,
    PositionClosedPayload,
    PositionOpenedPayload,
    SignalCreatedPayload,
    PortfolioUpdatePayload,
    AnalyticsUpdatePayload,
)

__all__ = [
    "manager",
    "websocket_router",
    "EventType",
    "WebSocketEvent",
    "PositionUpdatePayload",
    "PositionsBatchPayload",
    "PositionClosedPayload",
    "PositionOpenedPayload",
    "SignalCreatedPayload",
    "PortfolioUpdatePayload",
    "AnalyticsUpdatePayload",
]
