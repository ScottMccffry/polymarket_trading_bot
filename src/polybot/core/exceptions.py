"""Custom exceptions for the trading bot."""


class PolybotError(Exception):
    """Base exception for all polybot errors."""

    pass


class ConfigurationError(PolybotError):
    """Raised when there's a configuration problem."""

    pass


class TradingError(PolybotError):
    """Base exception for trading-related errors."""

    pass


class InsufficientCapitalError(TradingError):
    """Raised when there's not enough capital for a trade."""

    pass


class MarketNotFoundError(TradingError):
    """Raised when a market cannot be found."""

    pass


class PositionNotFoundError(TradingError):
    """Raised when a position cannot be found."""

    pass


class SignalNotFoundError(TradingError):
    """Raised when a signal cannot be found."""

    pass


class StrategyNotFoundError(TradingError):
    """Raised when a strategy cannot be found."""

    pass


class PriceFetchError(TradingError):
    """Raised when price data cannot be fetched."""

    pass


class TelegramError(PolybotError):
    """Raised for Telegram-related errors."""

    pass


class LLMError(PolybotError):
    """Raised for LLM/OpenAI-related errors."""

    pass


class QdrantError(PolybotError):
    """Raised for Qdrant-related errors."""

    pass
