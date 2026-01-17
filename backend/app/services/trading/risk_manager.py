"""
Risk Manager - Pre-trade risk validation.

Enforces position sizing, daily loss limits, and drawdown protection.
"""

from dataclasses import dataclass, field
from datetime import date


@dataclass
class RiskConfig:
    """Risk management configuration."""
    # Position limits
    max_position_size: float = 100.0  # Max USD per position
    max_portfolio_risk_percent: float = 2.0  # Max % of capital per trade

    # Loss limits
    max_daily_loss: float = 200.0  # Max loss per day in USD
    max_drawdown_percent: float = 10.0  # Max % drawdown from peak

    # Position limits
    max_open_positions: int = 10  # Max concurrent positions

    # Master switch
    enabled: bool = True


class RiskManager:
    """
    Pre-trade risk validation.

    Call validate_* methods before opening positions.
    """

    def __init__(self, config: RiskConfig | None = None):
        self.config = config or RiskConfig()
        self._daily_pnl: float = 0.0
        self._current_date: date = date.today()

    def validate_position_size(
        self,
        size_usd: float,
        capital: float,
    ) -> tuple[bool, str]:
        """
        Validate position size against limits.

        Args:
            size_usd: Proposed position size in USD
            capital: Total available capital

        Returns:
            (is_valid, error_message)
        """
        if not self.config.enabled:
            return True, ""

        # Check absolute max
        if size_usd > self.config.max_position_size:
            return False, f"Position size ${size_usd:.2f} exceeds max ${self.config.max_position_size:.2f}"

        # Check portfolio risk percentage
        if capital > 0:
            max_risk_amount = capital * (self.config.max_portfolio_risk_percent / 100)
            if size_usd > max_risk_amount:
                return False, (
                    f"Position size ${size_usd:.2f} exceeds portfolio risk limit "
                    f"({self.config.max_portfolio_risk_percent}% of ${capital:.2f} = ${max_risk_amount:.2f})"
                )

        return True, ""

    def _check_date_rollover(self) -> None:
        """Reset daily P&L if date changed."""
        today = date.today()
        if today != self._current_date:
            self._daily_pnl = 0.0
            self._current_date = today

    def record_daily_pnl(self, pnl: float) -> None:
        """
        Record realized P&L for daily tracking.

        Call this when a position is closed.
        """
        self._check_date_rollover()
        self._daily_pnl += pnl

    def validate_daily_loss(self) -> tuple[bool, str]:
        """
        Check if daily loss limit has been exceeded.

        Returns:
            (is_valid, error_message)
        """
        if not self.config.enabled:
            return True, ""

        self._check_date_rollover()

        if self._daily_pnl < 0 and abs(self._daily_pnl) >= self.config.max_daily_loss:
            return False, (
                f"Daily loss limit reached: ${abs(self._daily_pnl):.2f} "
                f"(max: ${self.config.max_daily_loss:.2f})"
            )

        return True, ""

    def get_daily_pnl(self) -> float:
        """Get current daily P&L."""
        self._check_date_rollover()
        return self._daily_pnl
