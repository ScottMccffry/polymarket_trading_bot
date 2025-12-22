"""Telegram message monitor for polling groups."""

import asyncio
from datetime import datetime, timezone
from telethon.tl.types import Message
import structlog

from .client import TelegramService
from ...config import get_settings
from ...core.events import MessageReceived
from ...core.bus import EventBus

logger = structlog.get_logger()


class TelegramMonitor:
    """Monitors Telegram groups for new messages."""

    def __init__(self, event_bus: EventBus) -> None:
        self.settings = get_settings()
        self.event_bus = event_bus
        self.telegram = TelegramService()

        # Track last seen message IDs per chat
        self._last_message_ids: dict[int, int] = {}
        self._running = False
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        """Start monitoring Telegram groups."""
        await self.telegram.connect()
        self._running = True

        # Initial swipe - get last few messages from each group
        for group in self.settings.telegram_groups:
            await self._initial_swipe(group)

        # Start polling loop
        self._task = asyncio.create_task(self._poll_loop())
        logger.info(
            "telegram_monitor_started",
            groups=self.settings.telegram_groups,
            interval=self.settings.telegram_check_interval,
        )

    async def stop(self) -> None:
        """Stop monitoring."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        await self.telegram.disconnect()
        logger.info("telegram_monitor_stopped")

    async def _initial_swipe(self, group_name: str) -> None:
        """Fetch last 3 messages from a group on startup."""
        try:
            entity = await self.telegram.get_entity(group_name)
            messages = await self.telegram.get_messages(entity, limit=3)

            for msg in reversed(messages):
                if msg.text:
                    self._last_message_ids[msg.chat_id] = msg.id
                    await self._process_message(msg, getattr(entity, "title", group_name))

            logger.debug("initial_swipe_complete", group=group_name, count=len(messages))
        except Exception as e:
            logger.error("initial_swipe_error", group=group_name, error=str(e))

    async def _poll_loop(self) -> None:
        """Main polling loop."""
        while self._running:
            try:
                for group in self.settings.telegram_groups:
                    await self._check_group(group)
                await asyncio.sleep(self.settings.telegram_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("poll_loop_error", error=str(e))
                await asyncio.sleep(10)  # Brief pause on error

    async def _check_group(self, group_name: str) -> None:
        """Check a group for new messages."""
        try:
            entity = await self.telegram.get_entity(group_name)
            chat_id = entity.id
            last_id = self._last_message_ids.get(chat_id, 0)

            messages = await self.telegram.get_messages(
                entity,
                limit=50,
                min_id=last_id,
            )

            new_count = 0
            for msg in reversed(messages):
                if msg.text and msg.id > last_id:
                    self._last_message_ids[chat_id] = msg.id
                    await self._process_message(msg, getattr(entity, "title", group_name))
                    new_count += 1

            if new_count > 0:
                logger.debug("new_messages", group=group_name, count=new_count)

        except Exception as e:
            logger.error("check_group_error", group=group_name, error=str(e))

    async def _process_message(self, msg: Message, chat_title: str) -> None:
        """Process a message and publish event."""
        event = MessageReceived(
            message_id=msg.id,
            chat_id=msg.chat_id,
            chat_title=chat_title,
            text=msg.text or "",
            sender=str(msg.sender_id) if msg.sender_id else "",
            timestamp=msg.date or datetime.now(timezone.utc),
        )
        await self.event_bus.publish(event)
        logger.debug(
            "message_received",
            chat=chat_title,
            message_id=msg.id,
            text_length=len(msg.text or ""),
        )
