"""Telegram message monitoring service."""
import asyncio
import logging
from datetime import datetime, UTC
from typing import Callable, Awaitable

from .client import TelegramService, TelegramMessage
from ...config import Settings, get_settings

logger = logging.getLogger(__name__)


class TelegramMonitor:
    """Monitor Telegram groups for new messages."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self.service = TelegramService(self.settings)
        self.last_message_ids: dict[str, int] = {}
        self._running = False

    def _get_groups(self) -> list[str]:
        """Parse monitored groups from config."""
        if not self.settings.telegram_monitored_groups:
            return []
        return [g.strip() for g in self.settings.telegram_monitored_groups.split(",") if g.strip()]

    async def start(self):
        """Start the Telegram client."""
        await self.service.start()

    async def stop(self):
        """Stop the monitor."""
        self._running = False
        await self.service.disconnect()

    async def monitor(
        self,
        callback: Callable[[TelegramMessage], Awaitable[None]],
        groups: list[str] | None = None,
        first_swipe_count: int = 3,
        max_age_minutes: int = 30,
    ):
        """Monitor groups for new messages."""
        await self.start()
        self._running = True

        groups = groups or self._get_groups()
        if not groups:
            raise ValueError("No groups to monitor")

        logger.info(f"[TELEGRAM] Monitoring {len(groups)} groups: {groups}")

        # First swipe - process recent messages
        if first_swipe_count > 0:
            await self._first_swipe(groups, callback, first_swipe_count, max_age_minutes)

        # Main polling loop
        try:
            while self._running:
                for group in groups:
                    await self._check_group(group, callback)
                await asyncio.sleep(self.settings.telegram_check_interval)
        finally:
            await self.stop()

    async def _first_swipe(
        self,
        groups: list[str],
        callback: Callable[[TelegramMessage], Awaitable[None]],
        count: int,
        max_age_minutes: int,
    ):
        """Process recent messages on startup."""
        for group in groups:
            try:
                messages = await self.service.get_recent_messages(group, limit=count)
                if not messages:
                    continue

                # Process oldest first
                messages.reverse()

                for msg in messages:
                    # Track latest ID
                    if group not in self.last_message_ids or msg.message_id > self.last_message_ids[group]:
                        self.last_message_ids[group] = msg.message_id

                    # Skip old messages
                    age = (datetime.now(UTC) - msg.timestamp.replace(tzinfo=UTC)).total_seconds() / 60
                    if age > max_age_minutes:
                        continue

                    logger.info(f"[TELEGRAM] First swipe: {msg.chat_title} - {msg.text[:50]}...")
                    await callback(msg)

            except Exception as e:
                logger.error(f"[TELEGRAM] First swipe error for {group}: {e}")

    async def _check_group(
        self,
        group: str,
        callback: Callable[[TelegramMessage], Awaitable[None]],
    ):
        """Check a single group for new messages."""
        try:
            msg = await self.service.get_last_message(group)
            if not msg:
                return

            cached_id = self.last_message_ids.get(group)

            if cached_id is None:
                # First time - only process if recent (< 20 min)
                age = (datetime.now(UTC) - msg.timestamp.replace(tzinfo=UTC)).total_seconds()
                if age < 1200:
                    logger.info(f"[TELEGRAM] New message: {msg.chat_title} - {msg.text[:50]}...")
                    await callback(msg)
                self.last_message_ids[group] = msg.message_id

            elif msg.message_id > cached_id:
                # New message since last check
                logger.info(f"[TELEGRAM] New message: {msg.chat_title} - {msg.text[:50]}...")
                await callback(msg)
                self.last_message_ids[group] = msg.message_id

        except Exception as e:
            logger.error(f"[TELEGRAM] Error checking {group}: {e}")
