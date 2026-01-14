"""
Bot Orchestrator - Main trading bot loop manager.

Controls the lifecycle of the trading bot and manages background tasks.
"""

import asyncio
import logging
from datetime import datetime
from typing import Callable, Awaitable, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class BotStatus(str, Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


class BotTask:
    """Represents a recurring bot task."""

    def __init__(
        self,
        name: str,
        func: Callable[[], Awaitable[None]],
        interval_seconds: int,
        enabled: bool = True,
    ):
        self.name = name
        self.func = func
        self.interval_seconds = interval_seconds
        self.enabled = enabled
        self.last_run: Optional[datetime] = None
        self.run_count: int = 0
        self.error_count: int = 0
        self.last_error: Optional[str] = None


class BotOrchestrator:
    """
    Main trading bot orchestrator.

    Manages the bot lifecycle and runs registered tasks in a loop.

    Usage:
        orchestrator = BotOrchestrator()

        # Register tasks
        orchestrator.register_task("position_check", check_positions, interval=60)
        orchestrator.register_task("signal_sniper", snipe_signals, interval=30)

        # Start the bot
        await orchestrator.start()

        # Stop the bot
        await orchestrator.stop()
    """

    def __init__(self):
        self._status: BotStatus = BotStatus.STOPPED
        self._tasks: dict[str, BotTask] = {}
        self._running_tasks: list[asyncio.Task] = []
        self._started_at: Optional[datetime] = None
        self._stopped_at: Optional[datetime] = None
        self._error_message: Optional[str] = None
        self._loop_task: Optional[asyncio.Task] = None

    @property
    def status(self) -> BotStatus:
        return self._status

    @property
    def is_running(self) -> bool:
        return self._status == BotStatus.RUNNING

    def register_task(
        self,
        name: str,
        func: Callable[[], Awaitable[None]],
        interval_seconds: int,
        enabled: bool = True,
    ) -> None:
        """Register a recurring task to run in the bot loop."""
        self._tasks[name] = BotTask(
            name=name,
            func=func,
            interval_seconds=interval_seconds,
            enabled=enabled,
        )
        logger.info(f"Registered bot task: {name} (interval: {interval_seconds}s)")

    def unregister_task(self, name: str) -> None:
        """Remove a task from the bot."""
        if name in self._tasks:
            del self._tasks[name]
            logger.info(f"Unregistered bot task: {name}")

    def enable_task(self, name: str) -> None:
        """Enable a registered task."""
        if name in self._tasks:
            self._tasks[name].enabled = True

    def disable_task(self, name: str) -> None:
        """Disable a registered task without removing it."""
        if name in self._tasks:
            self._tasks[name].enabled = False

    async def start(self) -> dict:
        """Start the trading bot."""
        if self._status == BotStatus.RUNNING:
            return {"status": "already_running", "message": "Bot is already running"}

        if self._status == BotStatus.STARTING:
            return {"status": "starting", "message": "Bot is already starting"}

        try:
            self._status = BotStatus.STARTING
            self._error_message = None
            logger.info("Starting bot orchestrator...")

            # Start task loops
            self._running_tasks = []
            for task_name, task in self._tasks.items():
                if task.enabled:
                    asyncio_task = asyncio.create_task(
                        self._run_task_loop(task),
                        name=f"bot_task_{task_name}"
                    )
                    self._running_tasks.append(asyncio_task)
                    logger.info(f"Started task loop: {task_name}")

            self._status = BotStatus.RUNNING
            self._started_at = datetime.utcnow()
            self._stopped_at = None

            logger.info(f"Bot orchestrator started with {len(self._running_tasks)} tasks")
            return {
                "status": "started",
                "message": f"Bot started with {len(self._running_tasks)} active tasks",
                "tasks": [t for t, task in self._tasks.items() if task.enabled],
            }

        except Exception as e:
            self._status = BotStatus.ERROR
            self._error_message = str(e)
            logger.error(f"Failed to start bot: {e}")
            return {"status": "error", "message": str(e)}

    async def stop(self) -> dict:
        """Stop the trading bot."""
        if self._status == BotStatus.STOPPED:
            return {"status": "already_stopped", "message": "Bot is already stopped"}

        if self._status == BotStatus.STOPPING:
            return {"status": "stopping", "message": "Bot is already stopping"}

        try:
            self._status = BotStatus.STOPPING
            logger.info("Stopping bot orchestrator...")

            # Cancel all running tasks
            for task in self._running_tasks:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

            self._running_tasks = []
            self._status = BotStatus.STOPPED
            self._stopped_at = datetime.utcnow()

            logger.info("Bot orchestrator stopped")
            return {"status": "stopped", "message": "Bot stopped successfully"}

        except Exception as e:
            self._status = BotStatus.ERROR
            self._error_message = str(e)
            logger.error(f"Error stopping bot: {e}")
            return {"status": "error", "message": str(e)}

    async def _run_task_loop(self, task: BotTask) -> None:
        """Run a single task in a loop."""
        logger.info(f"Task loop started: {task.name}")

        while self._status == BotStatus.RUNNING:
            try:
                if task.enabled:
                    logger.debug(f"Running task: {task.name}")
                    await task.func()
                    task.last_run = datetime.utcnow()
                    task.run_count += 1
                    task.last_error = None

            except asyncio.CancelledError:
                logger.info(f"Task cancelled: {task.name}")
                raise
            except Exception as e:
                task.error_count += 1
                task.last_error = str(e)
                logger.error(f"Error in task {task.name}: {e}")

            # Wait for next interval
            await asyncio.sleep(task.interval_seconds)

        logger.info(f"Task loop ended: {task.name}")

    def get_status(self) -> dict:
        """Get current bot status and task information."""
        task_info = []
        for name, task in self._tasks.items():
            task_info.append({
                "name": name,
                "enabled": task.enabled,
                "interval_seconds": task.interval_seconds,
                "last_run": task.last_run.isoformat() if task.last_run else None,
                "run_count": task.run_count,
                "error_count": task.error_count,
                "last_error": task.last_error,
            })

        return {
            "status": self._status.value,
            "is_running": self.is_running,
            "started_at": self._started_at.isoformat() if self._started_at else None,
            "stopped_at": self._stopped_at.isoformat() if self._stopped_at else None,
            "uptime_seconds": (
                (datetime.utcnow() - self._started_at).total_seconds()
                if self._started_at and self.is_running
                else None
            ),
            "error_message": self._error_message,
            "tasks": task_info,
            "active_task_count": len([t for t in self._tasks.values() if t.enabled]),
        }


# Global singleton instance
bot_orchestrator = BotOrchestrator()


# ============================================================================
# Default Tasks - You can add your own tasks here
# ============================================================================

async def _placeholder_position_check():
    """
    Placeholder for position check task.
    Replace with actual implementation that calls:
    - apply_strategy_to_open_positions()
    """
    logger.debug("[BOT] Position check placeholder - implement your logic here")
    # TODO: Import and call your position check logic
    # from app.services.trading.executor import TradingExecutor
    # executor = TradingExecutor()
    # async with get_db_context() as db:
    #     await executor.check_all_positions(db)


async def _placeholder_signal_sniper():
    """
    Placeholder for signal sniper task.
    Replace with actual implementation that:
    - Polls Telegram for new messages
    - Runs LLM analysis to extract signals
    - Opens positions based on signals
    """
    logger.debug("[BOT] Signal sniper placeholder - implement your logic here")
    # TODO: Implement snipe_insider() logic


async def _placeholder_easy_wins():
    """
    Placeholder for easy wins monitor task.
    Replace with actual implementation that:
    - Scans markets for high probability opportunities
    - Automatically enters positions
    """
    logger.debug("[BOT] Easy wins placeholder - implement your logic here")
    # TODO: Implement monitor_easy_wins_markets() logic


async def _placeholder_high_frequency():
    """
    Placeholder for high frequency trading task.
    Runs every second for real-time market monitoring.

    Replace with actual implementation that:
    - Monitors price movements in real-time
    - Detects rapid price changes or arbitrage opportunities
    - Updates position prices for live P&L tracking
    - Executes time-sensitive trades
    """
    logger.debug("[BOT] High frequency placeholder - implement your logic here")
    # TODO: Implement high frequency trading logic
    # Examples:
    # - await update_all_position_prices()
    # - await check_arbitrage_opportunities()
    # - await monitor_whale_movements()


def register_default_tasks():
    """Register the default bot tasks. Call this at startup."""
    # Position check - runs every 60 seconds
    bot_orchestrator.register_task(
        name="position_check",
        func=_placeholder_position_check,
        interval_seconds=60,
        enabled=True,
    )

    # Signal sniper - runs every 30 seconds
    bot_orchestrator.register_task(
        name="signal_sniper",
        func=_placeholder_signal_sniper,
        interval_seconds=30,
        enabled=False,  # Disabled until implemented
    )

    # Easy wins monitor - runs every 5 minutes
    bot_orchestrator.register_task(
        name="easy_wins",
        func=_placeholder_easy_wins,
        interval_seconds=300,
        enabled=False,  # Disabled until implemented
    )

    # High frequency trading - runs every second
    bot_orchestrator.register_task(
        name="high_frequency",
        func=_placeholder_high_frequency,
        interval_seconds=1,
        enabled=False,  # Disabled until implemented (WARNING: high resource usage)
    )
