"""Telegram client service."""
import logging
from dataclasses import dataclass
from datetime import datetime, UTC
from pathlib import Path

from telethon import TelegramClient
from telethon.tl.types import Message

from ...config import Settings, get_settings

logger = logging.getLogger(__name__)


@dataclass
class TelegramMessage:
    """Telegram message data."""
    message_id: int
    chat_id: int
    chat_title: str
    text: str
    timestamp: datetime


class TelegramService:
    """Telegram client wrapper for fetching messages."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self.client: TelegramClient | None = None
        self._using_shared_client = False

    def _get_session_path(self) -> str:
        """Get session file path."""
        path = Path(self.settings.telegram_session_path)
        path.mkdir(parents=True, exist_ok=True)
        return str(path / "session")

    async def start(self):
        """Start client using existing session."""
        # Try to reuse client from TelegramAuth
        try:
            from .auth import telegram_auth
            existing = telegram_auth.get_client()
            if existing and existing.is_connected():
                logger.info("[TELEGRAM] Reusing authenticated client")
                self.client = existing
                self._using_shared_client = True
                return
        except Exception as e:
            logger.debug(f"[TELEGRAM] Could not reuse auth client: {e}")

        self._using_shared_client = False

        if not self.settings.telegram_api_id:
            raise ValueError("TELEGRAM_API_ID not configured")

        session_path = self._get_session_path()
        self.client = TelegramClient(
            session_path,
            self.settings.telegram_api_id,
            self.settings.telegram_api_hash,
        )

        await self.client.connect()

        if not await self.client.is_user_authorized():
            raise RuntimeError("Not authenticated. Connect Telegram first.")

        logger.info("[TELEGRAM] Client started")

    async def disconnect(self):
        """Disconnect client (unless shared)."""
        if self.client and not self._using_shared_client:
            await self.client.disconnect()
        self.client = None

    async def get_last_message(self, group: str) -> TelegramMessage | None:
        """Get the most recent message from a group."""
        if not self.client:
            raise RuntimeError("Client not started")

        try:
            entity = await self.client.get_entity(group)
            messages = await self.client.get_messages(entity, limit=1)

            if not messages or not messages[0].text:
                return None

            msg: Message = messages[0]
            return TelegramMessage(
                message_id=msg.id,
                chat_id=entity.id,
                chat_title=getattr(entity, "title", group),
                text=msg.text,
                timestamp=msg.date,
            )
        except Exception as e:
            logger.error(f"[TELEGRAM] Error getting message from {group}: {e}")
            return None

    async def get_recent_messages(self, group: str, limit: int = 5) -> list[TelegramMessage]:
        """Get the most recent N messages from a group."""
        if not self.client:
            raise RuntimeError("Client not started")

        try:
            entity = await self.client.get_entity(group)
            messages = await self.client.get_messages(entity, limit=limit)

            result = []
            for msg in messages:
                if msg.text:
                    result.append(TelegramMessage(
                        message_id=msg.id,
                        chat_id=entity.id,
                        chat_title=getattr(entity, "title", group),
                        text=msg.text,
                        timestamp=msg.date,
                    ))

            return result
        except Exception as e:
            logger.error(f"[TELEGRAM] Error getting messages from {group}: {e}")
            return []
