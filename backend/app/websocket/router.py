"""WebSocket endpoint router."""
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from jose import JWTError, jwt

from ..config import get_settings
from .manager import manager
from .events import EventType, WebSocketEvent

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(tags=["websocket"])


async def authenticate_websocket(token: str | None) -> int | None:
    """
    Validate JWT token and return user_id.
    Returns None if authentication fails (anonymous connection allowed).
    """
    if not token:
        return None

    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        email = payload.get("sub")
        if email:
            # Return hash of email as user_id for now
            # In production, would look up actual user_id from database
            return hash(email) % (10**9)
        return None
    except JWTError as e:
        logger.warning(f"[WebSocket] JWT validation failed: {e}")
        return None


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str | None = Query(default=None)
):
    """
    WebSocket endpoint for real-time updates.

    Authentication is optional - unauthenticated clients receive all broadcasts.
    Authenticated clients can receive user-specific messages.

    Connect: ws://localhost:8000/ws or ws://localhost:8000/ws?token=YOUR_JWT

    Events received by clients:
    - positions_batch: When positions are checked and updated
    - position_closed: When a position is closed
    - position_opened: When a new position is opened
    - signal_created: When a new signal is detected
    - portfolio_update: When portfolio stats change

    Client can send:
    - {"type": "ping"} - Server responds with {"type": "pong"}
    """
    user_id = await authenticate_websocket(token)
    await manager.connect(websocket, user_id)

    try:
        while True:
            # Wait for client messages
            data = await websocket.receive_json()

            # Handle client pings
            if data.get("type") == "ping":
                pong_event = WebSocketEvent.create(EventType.PONG, {})
                await manager.send_to_connection(websocket, pong_event.model_dump())

            # Future: could add subscription management here
            # e.g., subscribe to specific position IDs

    except WebSocketDisconnect:
        logger.info("[WebSocket] Client disconnected gracefully")
        await manager.disconnect(websocket, user_id)
    except Exception as e:
        logger.error(f"[WebSocket] Connection error: {e}")
        await manager.disconnect(websocket, user_id)


@router.get("/ws/status")
async def websocket_status():
    """Get WebSocket connection status."""
    return manager.get_status()
