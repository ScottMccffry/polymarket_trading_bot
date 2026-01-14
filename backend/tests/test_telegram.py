"""Tests for Telegram services."""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, UTC

from app.services.telegram.auth import TelegramAuth
from app.services.telegram.client import TelegramService, TelegramMessage
from app.services.telegram.monitor import TelegramMonitor
from app.config import Settings


class TestTelegramAuth:
    """Test suite for TelegramAuth."""

    def setup_method(self):
        """Reset singleton state before each test."""
        TelegramAuth._instance = None
        TelegramAuth._client = None
        TelegramAuth._authenticated = False
        TelegramAuth._awaiting_code = False
        TelegramAuth._error = None

    def test_singleton(self):
        """Test TelegramAuth is a singleton."""
        auth1 = TelegramAuth.get_instance()
        auth2 = TelegramAuth.get_instance()
        assert auth1 is auth2

    def test_status_not_configured(self):
        """Test status when not configured."""
        auth = TelegramAuth.get_instance()
        status = auth.status()
        assert status["authenticated"] is False
        assert status["awaiting_code"] is False

    @patch("app.services.telegram.auth.get_settings")
    @pytest.mark.asyncio
    async def test_connect_missing_api_id(self, mock_settings):
        """Test connect fails without API ID."""
        mock_settings.return_value = Settings(telegram_api_id=0)
        auth = TelegramAuth.get_instance()
        result = await auth.connect()
        assert result["success"] is False
        assert "API ID" in result["error"]

    @patch("app.services.telegram.auth.get_settings")
    @pytest.mark.asyncio
    async def test_connect_missing_phone(self, mock_settings):
        """Test connect fails without phone."""
        mock_settings.return_value = Settings(
            telegram_api_id=12345,
            telegram_api_hash="hash123",
            telegram_phone=""
        )
        auth = TelegramAuth.get_instance()
        result = await auth.connect()
        assert result["success"] is False
        assert "Phone" in result["error"]

    @patch("app.services.telegram.auth.TelegramClient")
    @patch("app.services.telegram.auth.get_settings")
    @pytest.mark.asyncio
    async def test_connect_already_authorized(self, mock_settings, mock_client_class):
        """Test connect when already authorized."""
        mock_settings.return_value = Settings(
            telegram_api_id=12345,
            telegram_api_hash="hash123",
            telegram_phone="+1234567890",
            telegram_session_path="/tmp/test_telegram"
        )

        mock_client = AsyncMock()
        mock_client.is_user_authorized = AsyncMock(return_value=True)
        mock_client_class.return_value = mock_client

        auth = TelegramAuth.get_instance()
        result = await auth.connect()

        assert result["success"] is True
        assert result["authenticated"] is True

    @patch("app.services.telegram.auth.TelegramClient")
    @patch("app.services.telegram.auth.get_settings")
    @pytest.mark.asyncio
    async def test_connect_sends_code(self, mock_settings, mock_client_class):
        """Test connect sends verification code."""
        mock_settings.return_value = Settings(
            telegram_api_id=12345,
            telegram_api_hash="hash123",
            telegram_phone="+1234567890",
            telegram_session_path="/tmp/test_telegram"
        )

        mock_client = AsyncMock()
        mock_client.is_user_authorized = AsyncMock(return_value=False)
        mock_client_class.return_value = mock_client

        auth = TelegramAuth.get_instance()
        result = await auth.connect()

        assert result["success"] is True
        assert result["authenticated"] is False
        assert result["awaiting_code"] is True
        mock_client.send_code_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_verify_code_not_connected(self):
        """Test verify fails when not connected."""
        auth = TelegramAuth.get_instance()
        result = await auth.verify_code("12345")
        assert result["success"] is False
        assert "Not connected" in result["error"]


class TestTelegramService:
    """Test suite for TelegramService."""

    @patch("app.services.telegram.client.TelegramClient")
    @pytest.mark.asyncio
    async def test_start_not_authorized(self, mock_client_class):
        """Test start fails when not authorized."""
        mock_client = AsyncMock()
        mock_client.is_user_authorized = AsyncMock(return_value=False)
        mock_client_class.return_value = mock_client

        settings = Settings(
            telegram_api_id=12345,
            telegram_api_hash="hash123",
            telegram_session_path="/tmp/test_telegram"
        )
        service = TelegramService(settings)

        with pytest.raises(RuntimeError, match="Not authenticated"):
            await service.start()

    @patch("app.services.telegram.client.TelegramClient")
    @pytest.mark.asyncio
    async def test_get_last_message(self, mock_client_class):
        """Test getting last message from group."""
        mock_message = MagicMock()
        mock_message.id = 123
        mock_message.text = "Test message"
        mock_message.date = datetime.now(UTC)

        mock_entity = MagicMock()
        mock_entity.id = 456
        mock_entity.title = "Test Group"

        mock_client = AsyncMock()
        mock_client.is_user_authorized = AsyncMock(return_value=True)
        mock_client.get_entity = AsyncMock(return_value=mock_entity)
        mock_client.get_messages = AsyncMock(return_value=[mock_message])
        mock_client_class.return_value = mock_client

        settings = Settings(
            telegram_api_id=12345,
            telegram_api_hash="hash123",
            telegram_session_path="/tmp/test_telegram"
        )
        service = TelegramService(settings)
        await service.start()

        msg = await service.get_last_message("test_group")

        assert msg is not None
        assert msg.message_id == 123
        assert msg.text == "Test message"
        assert msg.chat_title == "Test Group"

    @patch("app.services.telegram.client.TelegramClient")
    @pytest.mark.asyncio
    async def test_get_recent_messages(self, mock_client_class):
        """Test getting recent messages."""
        mock_messages = [
            MagicMock(id=1, text="Message 1", date=datetime.now(UTC)),
            MagicMock(id=2, text="Message 2", date=datetime.now(UTC)),
            MagicMock(id=3, text=None, date=datetime.now(UTC)),  # No text
        ]

        mock_entity = MagicMock()
        mock_entity.id = 456
        mock_entity.title = "Test Group"

        mock_client = AsyncMock()
        mock_client.is_user_authorized = AsyncMock(return_value=True)
        mock_client.get_entity = AsyncMock(return_value=mock_entity)
        mock_client.get_messages = AsyncMock(return_value=mock_messages)
        mock_client_class.return_value = mock_client

        settings = Settings(
            telegram_api_id=12345,
            telegram_api_hash="hash123",
            telegram_session_path="/tmp/test_telegram"
        )
        service = TelegramService(settings)
        await service.start()

        messages = await service.get_recent_messages("test_group", limit=3)

        # Should only include messages with text
        assert len(messages) == 2
        assert messages[0].text == "Message 1"
        assert messages[1].text == "Message 2"


class TestTelegramMonitor:
    """Test suite for TelegramMonitor."""

    def test_get_groups_empty(self):
        """Test getting groups when not configured."""
        settings = Settings(telegram_monitored_groups="")
        monitor = TelegramMonitor(settings)
        groups = monitor._get_groups()
        assert groups == []

    def test_get_groups_configured(self):
        """Test getting groups from config."""
        settings = Settings(telegram_monitored_groups="group1, group2, group3")
        monitor = TelegramMonitor(settings)
        groups = monitor._get_groups()
        assert groups == ["group1", "group2", "group3"]

    @patch.object(TelegramService, "start")
    @patch.object(TelegramService, "get_last_message")
    @pytest.mark.asyncio
    async def test_check_group_new_message(self, mock_get_msg, mock_start):
        """Test checking group detects new message."""
        mock_msg = TelegramMessage(
            message_id=100,
            chat_id=1,
            chat_title="Test",
            text="New message",
            timestamp=datetime.now(UTC)
        )
        mock_get_msg.return_value = mock_msg

        settings = Settings(telegram_monitored_groups="test")
        monitor = TelegramMonitor(settings)
        monitor.last_message_ids["test"] = 99  # Previous message ID

        callback_called = []
        async def callback(msg):
            callback_called.append(msg)

        await monitor._check_group("test", callback)

        assert len(callback_called) == 1
        assert callback_called[0].message_id == 100
        assert monitor.last_message_ids["test"] == 100

    @patch.object(TelegramService, "start")
    @patch.object(TelegramService, "get_last_message")
    @pytest.mark.asyncio
    async def test_check_group_no_new_message(self, mock_get_msg, mock_start):
        """Test checking group with same message."""
        mock_msg = TelegramMessage(
            message_id=100,
            chat_id=1,
            chat_title="Test",
            text="Same message",
            timestamp=datetime.now(UTC)
        )
        mock_get_msg.return_value = mock_msg

        settings = Settings(telegram_monitored_groups="test")
        monitor = TelegramMonitor(settings)
        monitor.last_message_ids["test"] = 100  # Same as current

        callback_called = []
        async def callback(msg):
            callback_called.append(msg)

        await monitor._check_group("test", callback)

        assert len(callback_called) == 0  # No callback since same message


class TestTelegramRoutes:
    """Test suite for Telegram API routes."""

    @pytest.mark.asyncio
    async def test_get_status(self, client):
        """Test /api/telegram/status endpoint."""
        response = await client.get("/api/telegram/status")
        assert response.status_code == 200
        data = response.json()
        assert "authenticated" in data
        assert "awaiting_code" in data

    @pytest.mark.asyncio
    async def test_get_groups(self, client):
        """Test /api/telegram/groups endpoint."""
        response = await client.get("/api/telegram/groups")
        assert response.status_code == 200
        data = response.json()
        assert "groups" in data
        assert isinstance(data["groups"], list)

    @patch("app.routes.telegram.telegram_auth")
    @pytest.mark.asyncio
    async def test_connect(self, mock_auth, client):
        """Test /api/telegram/connect endpoint."""
        mock_auth.connect = AsyncMock(return_value={
            "success": True,
            "awaiting_code": True,
            "message": "Code sent"
        })

        response = await client.post("/api/telegram/connect")
        assert response.status_code == 200
        data = response.json()
        assert data["awaiting_code"] is True

    @patch("app.routes.telegram.telegram_auth")
    @pytest.mark.asyncio
    async def test_connect_error(self, mock_auth, client):
        """Test /api/telegram/connect error handling."""
        mock_auth.connect = AsyncMock(return_value={
            "success": False,
            "error": "API not configured"
        })

        response = await client.post("/api/telegram/connect")
        assert response.status_code == 400

    @patch("app.routes.telegram.telegram_auth")
    @pytest.mark.asyncio
    async def test_verify_code(self, mock_auth, client):
        """Test /api/telegram/verify endpoint."""
        mock_auth.verify_code = AsyncMock(return_value={
            "success": True,
            "authenticated": True
        })

        response = await client.post(
            "/api/telegram/verify",
            json={"code": "12345"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] is True

    @patch("app.routes.telegram.telegram_auth")
    @pytest.mark.asyncio
    async def test_disconnect(self, mock_auth, client):
        """Test /api/telegram/disconnect endpoint."""
        mock_auth.disconnect = AsyncMock(return_value={
            "success": True,
            "message": "Disconnected"
        })

        response = await client.post("/api/telegram/disconnect")
        assert response.status_code == 200
