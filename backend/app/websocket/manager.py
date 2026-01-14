"""WebSocket connection manager."""
import asyncio
import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections with thread-safe operations.

    Uses singleton pattern - instantiated once and shared across the application.
    """
    _instance: "ConnectionManager | None" = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._connections: list[WebSocket] = []
            cls._instance._user_connections: dict[int, list[WebSocket]] = {}
            cls._instance._lock: asyncio.Lock | None = None
        return cls._instance

    @property
    def lock(self) -> asyncio.Lock:
        """Get or create the asyncio lock (must be created in async context)."""
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    async def connect(self, websocket: WebSocket, user_id: int | None = None):
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        async with self.lock:
            self._connections.append(websocket)
            if user_id is not None:
                if user_id not in self._user_connections:
                    self._user_connections[user_id] = []
                self._user_connections[user_id].append(websocket)
        logger.info(f"[WebSocket] Client connected. Total connections: {len(self._connections)}")

    async def disconnect(self, websocket: WebSocket, user_id: int | None = None):
        """Remove a WebSocket connection."""
        async with self.lock:
            if websocket in self._connections:
                self._connections.remove(websocket)
            if user_id is not None and user_id in self._user_connections:
                if websocket in self._user_connections[user_id]:
                    self._user_connections[user_id].remove(websocket)
                # Clean up empty user lists
                if not self._user_connections[user_id]:
                    del self._user_connections[user_id]
        logger.info(f"[WebSocket] Client disconnected. Total connections: {len(self._connections)}")

    async def broadcast(self, message: dict[str, Any]):
        """Broadcast message to all connected clients."""
        async with self.lock:
            connections = list(self._connections)

        if not connections:
            return

        disconnected: list[WebSocket] = []
        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"[WebSocket] Failed to send message to client: {e}")
                disconnected.append(connection)

        # Clean up disconnected clients
        for ws in disconnected:
            await self.disconnect(ws)

    async def send_to_user(self, user_id: int, message: dict[str, Any]):
        """Send message to specific user's connections."""
        async with self.lock:
            connections = self._user_connections.get(user_id, []).copy()

        disconnected: list[WebSocket] = []
        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"[WebSocket] Failed to send message to user {user_id}: {e}")
                disconnected.append(connection)

        # Clean up disconnected clients
        for ws in disconnected:
            await self.disconnect(ws, user_id)

    async def send_to_connection(self, websocket: WebSocket, message: dict[str, Any]):
        """Send message to a specific connection."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.warning(f"[WebSocket] Failed to send message: {e}")

    @property
    def connection_count(self) -> int:
        """Get the current number of connections."""
        return len(self._connections)

    def get_status(self) -> dict[str, Any]:
        """Get connection manager status."""
        return {
            "total_connections": len(self._connections),
            "users_connected": len(self._user_connections),
        }


# Global singleton instance
manager = ConnectionManager()
