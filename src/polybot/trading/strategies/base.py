"""Base strategy protocol and types."""

from typing import Protocol, NamedTuple
from datetime import datetime


class ExitDecision(NamedTuple):
    """Result of exit check."""

    should_exit: bool
    reason: str
    exit_percent: float = 1.0  # 1.0 = full exit, 0.5 = partial


class PositionContext(NamedTuple):
    """Context passed to strategy for decision making."""

    position_id: str
    entry_price: float
    current_price: float
    size: float
    capital_allocated: float
    side: str  # "Yes" or "No"
    peak_price: float | None
    opened_at: datetime
    hours_open: float


class Strategy(Protocol):
    """Protocol defining a trading strategy."""

    @property
    def name(self) -> str:
        """Strategy name identifier."""
        ...

    @property
    def description(self) -> str:
        """Human-readable description."""
        ...

    def should_enter(
        self,
        confidence: float,
        spread: float,
        price: float,
    ) -> bool:
        """Determine if strategy should take this signal.

        Args:
            confidence: LLM confidence score (0-1)
            spread: Bid-ask spread percentage
            price: Current ask price

        Returns:
            True if strategy accepts this signal
        """
        ...

    def should_exit(self, ctx: PositionContext) -> ExitDecision:
        """Determine if position should be exited.

        Args:
            ctx: Current position context

        Returns:
            ExitDecision with should_exit, reason, and exit_percent
        """
        ...

    def calculate_size(
        self,
        available_capital: float,
        confidence: float,
    ) -> float:
        """Calculate position size.

        Args:
            available_capital: Capital available for this position
            confidence: Signal confidence

        Returns:
            Capital amount to allocate
        """
        ...


def calculate_pnl_percent(
    entry_price: float,
    current_price: float,
    side: str,
) -> float:
    """Calculate P&L percentage.

    Args:
        entry_price: Entry price
        current_price: Current price
        side: "Yes" or "No"

    Returns:
        P&L as a decimal (0.1 = 10%)
    """
    if entry_price == 0:
        return 0.0

    if side.lower() == "yes":
        return (current_price - entry_price) / entry_price
    else:
        return (entry_price - current_price) / entry_price
