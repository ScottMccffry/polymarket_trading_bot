"""
Signal Trader - Real-time Telegram message processing and trading.

Monitors Telegram groups, analyzes messages against markets,
and opens positions based on signals.
"""

import logging
from typing import Optional

from app.database import get_db_context
from app.services.telegram.monitor import TelegramMonitor
from app.services.telegram.client import TelegramMessage
from app.services.trading.signal_generator import SignalGenerator, signal_generator
from app.services.trading.position_manager import PositionManager, position_manager

logger = logging.getLogger(__name__)


class SignalTrader:
    """
    Real-time signal trading from Telegram messages.

    Pipeline:
    1. Monitor Telegram groups for messages
    2. Search Qdrant for matching markets
    3. Analyze with LLM
    4. Generate signals
    5. Open positions
    """

    def __init__(
        self,
        signal_gen: Optional[SignalGenerator] = None,
        position_mgr: Optional[PositionManager] = None,
        strategy_name: str = "signal_trader",
        position_size: float = 50.0,
    ):
        self.telegram = TelegramMonitor()
        self.signal_gen = signal_gen or signal_generator
        self.position_mgr = position_mgr or position_manager
        self.strategy_name = strategy_name
        self.position_size = position_size
        self._running = False
        self._messages_processed = 0
        self._signals_created = 0
        self._positions_opened = 0

    async def on_message(self, msg: TelegramMessage) -> None:
        """
        Process a single Telegram message.

        Called by the TelegramMonitor for each new message.
        """
        try:
            self._messages_processed += 1
            logger.info(
                f"[SIGNAL_TRADER] Processing message from {msg.chat_title}: "
                f"{msg.text[:100]}..."
            )

            async with get_db_context() as db:
                # Generate signals from message
                signals = await self.signal_gen.process_message(
                    message=msg.text,
                    source=msg.chat_title or "telegram",
                    db=db,
                )

                if not signals:
                    logger.debug("[SIGNAL_TRADER] No actionable signals found")
                    return

                self._signals_created += len(signals)
                logger.info(f"[SIGNAL_TRADER] Generated {len(signals)} signals")

                # Open positions for signals
                positions = await self.position_mgr.open_positions_from_signals(
                    db=db,
                    signals=signals,
                    strategy_name=self.strategy_name,
                    size_per_position=self.position_size,
                )

                self._positions_opened += len(positions)
                logger.info(f"[SIGNAL_TRADER] Opened {len(positions)} positions")

        except Exception as e:
            logger.error(f"[SIGNAL_TRADER] Error processing message: {e}")

    async def run(self) -> None:
        """
        Start the signal trader.

        This runs the Telegram monitor with our callback.
        Blocks until stopped.
        """
        self._running = True
        logger.info("[SIGNAL_TRADER] Starting signal trader...")

        try:
            await self.telegram.monitor(callback=self.on_message)
        except Exception as e:
            logger.error(f"[SIGNAL_TRADER] Monitor error: {e}")
        finally:
            self._running = False
            logger.info("[SIGNAL_TRADER] Signal trader stopped")

    async def stop(self) -> None:
        """Stop the signal trader."""
        self._running = False
        await self.telegram.stop()

    def get_stats(self) -> dict:
        """Get current statistics."""
        return {
            "running": self._running,
            "messages_processed": self._messages_processed,
            "signals_created": self._signals_created,
            "positions_opened": self._positions_opened,
        }


# Singleton instance
signal_trader = SignalTrader()
