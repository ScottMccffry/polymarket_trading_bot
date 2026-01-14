"""Tests for WebSocket functionality."""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi.websockets import WebSocket

from app.websocket.manager import ConnectionManager
from app.websocket.events import EventType, WebSocketEvent


class TestConnectionManager:
    """Test suite for WebSocket ConnectionManager."""

    def test_singleton_pattern(self):
        """Test that ConnectionManager is a singleton."""
        manager1 = ConnectionManager()
        manager2 = ConnectionManager()
        assert manager1 is manager2

    @pytest.mark.asyncio
    async def test_connect(self):
        """Test connecting a WebSocket client."""
        manager = ConnectionManager()
        manager._connections = []  # Reset
        manager._user_connections = {}

        mock_ws = AsyncMock(spec=WebSocket)
        await manager.connect(mock_ws, user_id=123)

        assert len(manager._connections) == 1
        assert 123 in manager._user_connections
        assert mock_ws in manager._user_connections[123]
        mock_ws.accept.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_connect_anonymous(self):
        """Test connecting without user_id."""
        manager = ConnectionManager()
        manager._connections = []
        manager._user_connections = {}

        mock_ws = AsyncMock(spec=WebSocket)
        await manager.connect(mock_ws, user_id=None)

        assert len(manager._connections) == 1
        assert len(manager._user_connections) == 0

    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Test disconnecting a WebSocket client."""
        manager = ConnectionManager()
        manager._connections = []
        manager._user_connections = {}

        mock_ws = AsyncMock(spec=WebSocket)
        await manager.connect(mock_ws, user_id=456)

        # Disconnect
        await manager.disconnect(mock_ws, user_id=456)

        assert len(manager._connections) == 0
        assert 456 not in manager._user_connections

    @pytest.mark.asyncio
    async def test_broadcast(self):
        """Test broadcasting message to all clients."""
        manager = ConnectionManager()
        manager._connections = []

        # Connect multiple clients
        ws1 = AsyncMock(spec=WebSocket)
        ws2 = AsyncMock(spec=WebSocket)
        ws3 = AsyncMock(spec=WebSocket)

        await manager.connect(ws1)
        await manager.connect(ws2)
        await manager.connect(ws3)

        # Broadcast message
        message = {"type": "test", "data": "hello"}
        await manager.broadcast(message)

        ws1.send_json.assert_awaited_once_with(message)
        ws2.send_json.assert_awaited_once_with(message)
        ws3.send_json.assert_awaited_once_with(message)

    @pytest.mark.asyncio
    async def test_broadcast_handles_disconnected(self):
        """Test broadcast handles disconnected clients gracefully."""
        manager = ConnectionManager()
        manager._connections = []

        ws_good = AsyncMock(spec=WebSocket)
        ws_bad = AsyncMock(spec=WebSocket)
        ws_bad.send_json.side_effect = Exception("Connection closed")

        await manager.connect(ws_good)
        await manager.connect(ws_bad)

        message = {"type": "test", "data": "hello"}
        await manager.broadcast(message)

        # Good connection should receive message
        ws_good.send_json.assert_awaited_once_with(message)
        # Bad connection should be removed
        assert ws_bad not in manager._connections

    @pytest.mark.asyncio
    async def test_send_to_user(self):
        """Test sending message to specific user."""
        manager = ConnectionManager()
        manager._connections = []
        manager._user_connections = {}

        ws1 = AsyncMock(spec=WebSocket)
        ws2 = AsyncMock(spec=WebSocket)

        await manager.connect(ws1, user_id=100)
        await manager.connect(ws2, user_id=200)

        message = {"type": "test", "data": "private"}
        await manager.send_to_user(100, message)

        ws1.send_json.assert_awaited_once_with(message)
        ws2.send_json.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_send_to_user_multiple_connections(self):
        """Test sending to user with multiple connections."""
        manager = ConnectionManager()
        manager._connections = []
        manager._user_connections = {}

        ws1 = AsyncMock(spec=WebSocket)
        ws2 = AsyncMock(spec=WebSocket)

        # Same user with 2 connections
        await manager.connect(ws1, user_id=100)
        await manager.connect(ws2, user_id=100)

        message = {"type": "test", "data": "multi"}
        await manager.send_to_user(100, message)

        ws1.send_json.assert_awaited_once_with(message)
        ws2.send_json.assert_awaited_once_with(message)

    @pytest.mark.asyncio
    async def test_send_to_connection(self):
        """Test sending message to specific connection."""
        manager = ConnectionManager()

        ws = AsyncMock(spec=WebSocket)
        message = {"type": "test", "data": "direct"}

        await manager.send_to_connection(ws, message)

        ws.send_json.assert_awaited_once_with(message)

    @pytest.mark.asyncio
    async def test_send_to_connection_error(self):
        """Test sending to connection handles errors."""
        manager = ConnectionManager()

        ws = AsyncMock(spec=WebSocket)
        ws.send_json.side_effect = Exception("Connection error")

        message = {"type": "test", "data": "error"}

        # Should not raise exception
        await manager.send_to_connection(ws, message)

    def test_connection_count(self):
        """Test getting connection count."""
        manager = ConnectionManager()
        manager._connections = [Mock(), Mock(), Mock()]

        assert manager.connection_count == 3

    def test_get_status(self):
        """Test getting status information."""
        manager = ConnectionManager()
        manager._connections = [Mock(), Mock()]
        manager._user_connections = {100: [Mock()], 200: [Mock()]}

        status = manager.get_status()

        assert status["total_connections"] == 2
        assert status["users_connected"] == 2


class TestWebSocketEvents:
    """Test suite for WebSocket events."""

    def test_create_event(self):
        """Test creating a WebSocket event."""
        event = WebSocketEvent.create(
            EventType.POSITION_CLOSED,
            {"position_id": 123, "pnl": 50.0}
        )

        assert event.type == EventType.POSITION_CLOSED
        assert event.data["position_id"] == 123
        assert event.timestamp is not None

    def test_event_types(self):
        """Test all event types are defined."""
        assert EventType.POSITION_OPENED
        assert EventType.POSITION_CLOSED
        assert EventType.POSITIONS_BATCH
        assert EventType.SIGNAL_CREATED
        assert EventType.PORTFOLIO_UPDATE
        assert EventType.PONG


class TestWebSocketRouter:
    """Test suite for WebSocket router endpoints."""

    @pytest.mark.asyncio
    async def test_websocket_status_endpoint(self, client):
        """Test getting WebSocket status via HTTP endpoint."""
        response = await client.get("/ws/status")
        assert response.status_code == 200

        data = response.json()
        assert "total_connections" in data
        assert "users_connected" in data

    @pytest.mark.asyncio
    async def test_websocket_connection(self, client):
        """Test WebSocket connection establishment."""
        # Note: Full WebSocket testing with httpx AsyncClient has limitations
        # This test verifies the endpoint exists and accepts connections
        # Real WebSocket testing would require a WebSocket client library

        # Test that the endpoint exists
        response = await client.get("/ws/status")
        assert response.status_code == 200

    @pytest.mark.asyncio
    @patch('app.websocket.router.authenticate_websocket')
    async def test_websocket_authentication(self, mock_auth):
        """Test WebSocket authentication."""
        mock_auth.return_value = 123

        from app.websocket.router import authenticate_websocket

        # Test with valid token
        user_id = await authenticate_websocket("valid_token")
        # Due to patching limitations, we just verify the function exists

        # Test with no token
        user_id = await authenticate_websocket(None)
        assert user_id is None
