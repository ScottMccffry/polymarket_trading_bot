"""Telegram client wrapper using Telethon."""

from pathlib import Path
from telethon import TelegramClient
from telethon.tl.types import Message, User, Chat, Channel
import structlog

from ...config import get_settings
from ...core.exceptions import TelegramError

logger = structlog.get_logger()


class TelegramService:
    """Wrapper for Telethon Telegram client."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self._client: TelegramClient | None = None
        self._connected = False

    async def connect(self) -> None:
        """Connect to Telegram."""
        if self._connected:
            return

        if not self.settings.telegram_configured:
            raise TelegramError("Telegram not configured")

        # Ensure session directory exists
        session_path = Path("data/telegram")
        session_path.parent.mkdir(parents=True, exist_ok=True)

        self._client = TelegramClient(
            str(session_path),
            self.settings.telegram_api_id,
            self.settings.telegram_api_hash,
        )

        await self._client.start(phone=self.settings.telegram_phone)
        self._connected = True
        logger.info("telegram_connected")

    async def disconnect(self) -> None:
        """Disconnect from Telegram."""
        if self._client and self._connected:
            await self._client.disconnect()
            self._connected = False
            logger.info("telegram_disconnected")

    @property
    def client(self) -> TelegramClient:
        """Get the Telegram client."""
        if not self._client or not self._connected:
            raise TelegramError("Not connected to Telegram")
        return self._client

    async def get_entity(self, name: str) -> User | Chat | Channel:
        """Get a Telegram entity (user, chat, or channel) by name."""
        try:
            return await self.client.get_entity(name)
        except Exception as e:
            logger.error("get_entity_error", name=name, error=str(e))
            raise TelegramError(f"Failed to get entity {name}: {e}")

    async def get_messages(
        self,
        entity: str | User | Chat | Channel,
        limit: int = 10,
        min_id: int = 0,
    ) -> list[Message]:
        """Get messages from an entity.

        Args:
            entity: Entity name or object
            limit: Maximum number of messages
            min_id: Minimum message ID (for getting new messages only)

        Returns:
            List of Message objects
        """
        try:
            if isinstance(entity, str):
                entity = await self.get_entity(entity)

            messages = await self.client.get_messages(
                entity,
                limit=limit,
                min_id=min_id,
            )
            return list(messages)
        except Exception as e:
            logger.error("get_messages_error", error=str(e))
            raise TelegramError(f"Failed to get messages: {e}")

    async def get_me(self) -> User:
        """Get the current user."""
        return await self.client.get_me()

    @property
    def is_connected(self) -> bool:
        """Check if connected to Telegram."""
        return self._connected
