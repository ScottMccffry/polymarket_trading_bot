"""Base exit strategy class."""
from abc import ABC, abstractmethod


class ExitStrategy(ABC):
    """Abstract base class for exit strategies."""

    name: str = "base"

    @abstractmethod
    def should_exit(
        self, position: dict, current_price: float
    ) -> tuple[bool, str, float]:
        """
        Check if position should be exited.

        Args:
            position: Position dict with entry_price, capital_allocated, side, etc.
            current_price: Current market price

        Returns:
            (should_exit, reason, exit_percent)
            - should_exit: True if position should be exited
            - reason: Exit reason (take_profit, stop_loss, trailing_stop, etc.)
            - exit_percent: 1.0 for full exit, 0.5 for half, etc.
        """
        pass

    def _calc_pnl_percent(
        self, entry: float, current: float, capital: float, side: str = "Yes"
    ) -> float:
        """
        Calculate PnL percentage.

        Since we trade each token's own orderbook (YES token or NO token),
        both YES and NO positions profit when their token price goes UP.
        The formula is the same for both: (current - entry) * size
        """
        if capital <= 0 or entry <= 0:
            return 0.0
        # Same formula for both YES and NO - profit when token price goes up
        pnl = (current - entry) * (capital / entry)
        return (pnl / capital) * 100
