"""Main trading bot orchestrator."""

import asyncio
import structlog

from ..core.bus import EventBus
from ..core.events import MessageReceived
from ..services.telegram.monitor import TelegramMonitor
from ..services.polymarket.harvester import MarketHarvester
from ..trading.signals import SignalGenerator
from ..trading.positions import PositionManager
from ..trading.strategies.registry import StrategyRegistry
from ..db.session import get_session, init_db
from ..config import get_settings

logger = structlog.get_logger()


class TradingBot:
    """Main trading bot that orchestrates all components."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.event_bus = EventBus()
        self.strategy_registry = StrategyRegistry()
        self._running = False
        self._tasks: list[asyncio.Task] = []

    async def start(self) -> None:
        """Start the trading bot."""
        logger.info("bot_starting")

        # Initialize database
        await init_db()

        # Subscribe to events
        self.event_bus.subscribe(MessageReceived, self._on_message)

        self._running = True

        # Start event bus in background
        self._tasks.append(asyncio.create_task(self.event_bus.start()))

        # Start Telegram monitor if configured
        if self.settings.telegram_configured:
            self.telegram = TelegramMonitor(self.event_bus)
            await self.telegram.start()
        else:
            logger.warning("telegram_not_configured")
            self.telegram = None

        # Start background tasks
        self._tasks.append(asyncio.create_task(self._position_monitor_loop()))
        self._tasks.append(asyncio.create_task(self._market_refresh_loop()))

        logger.info("bot_started")

    async def _on_message(self, event: MessageReceived) -> None:
        """Handle incoming Telegram message."""
        logger.debug(
            "message_handler",
            chat=event.chat_title,
            text_length=len(event.text),
        )

        async with get_session() as session:
            # Generate signals
            generator = SignalGenerator(session, self.event_bus)
            signals = await generator.process_message(
                text=event.text,
                source=f"telegram:{event.chat_title}",
            )

            if signals:
                # Open positions for each signal
                manager = PositionManager(
                    session,
                    self.event_bus,
                    self.strategy_registry,
                )
                for signal in signals:
                    await manager.open_from_signal(signal)

    async def _position_monitor_loop(self) -> None:
        """Periodically check positions for exits."""
        logger.info("position_monitor_started")

        while self._running:
            try:
                await asyncio.sleep(60)  # Check every minute

                async with get_session() as session:
                    manager = PositionManager(
                        session,
                        self.event_bus,
                        self.strategy_registry,
                    )
                    closed = await manager.check_exits()

                    if closed:
                        logger.info("positions_closed", count=len(closed))

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("position_monitor_error", error=str(e))
                await asyncio.sleep(10)

    async def _market_refresh_loop(self) -> None:
        """Periodically refresh market data."""
        logger.info("market_refresh_started")

        while self._running:
            try:
                # Wait 12 hours between refreshes
                await asyncio.sleep(12 * 3600)

                harvester = MarketHarvester()
                count = await harvester.harvest()
                logger.info("markets_refreshed", count=count)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("market_refresh_error", error=str(e))
                await asyncio.sleep(60)

    async def stop(self) -> None:
        """Stop the trading bot."""
        logger.info("bot_stopping")
        self._running = False

        # Stop event bus
        self.event_bus.stop()

        # Stop Telegram monitor
        if self.telegram:
            await self.telegram.stop()

        # Cancel background tasks
        for task in self._tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        logger.info("bot_stopped")

    async def run_forever(self) -> None:
        """Run the bot until interrupted."""
        await self.start()
        try:
            while self._running:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass
        finally:
            await self.stop()
