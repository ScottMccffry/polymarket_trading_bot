"""Main entry point for the trading bot."""

import asyncio
import sys
import structlog

from .bot.orchestrator import TradingBot
from .config import get_settings

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


async def run_bot() -> None:
    """Run the trading bot."""
    settings = get_settings()
    logger.info(
        "starting_bot",
        telegram_groups=settings.telegram_groups,
        initial_capital=settings.initial_capital,
    )

    bot = TradingBot()

    try:
        await bot.run_forever()
    except KeyboardInterrupt:
        logger.info("keyboard_interrupt")
    except Exception as e:
        logger.exception("bot_error", error=str(e))
        sys.exit(1)


def main() -> None:
    """CLI entry point."""
    asyncio.run(run_bot())


if __name__ == "__main__":
    main()
