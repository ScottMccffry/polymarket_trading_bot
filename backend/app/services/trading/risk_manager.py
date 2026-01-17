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


@dataclass
class TradeValidationResult:
    """Result of pre-trade validation."""
    can_trade: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


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

    def validate_drawdown(
        self,
        current_equity: float,
        peak_equity: float,
    ) -> tuple[bool, str]:
        """
        Check if max drawdown has been exceeded.

        Args:
            current_equity: Current portfolio value
            peak_equity: Highest portfolio value recorded

        Returns:
            (is_valid, error_message)
        """
        if not self.config.enabled:
            return True, ""

        if peak_equity <= 0:
            return True, ""

        drawdown_pct = ((peak_equity - current_equity) / peak_equity) * 100

        if drawdown_pct >= self.config.max_drawdown_percent:
            return False, (
                f"Max drawdown exceeded: {drawdown_pct:.1f}% "
                f"(max: {self.config.max_drawdown_percent}%)"
            )

        return True, ""

    def validate_open_positions(self, current_count: int) -> tuple[bool, str]:
        """
        Check if we can open another position.

        Args:
            current_count: Number of currently open positions

        Returns:
            (is_valid, error_message)
        """
        if not self.config.enabled:
            return True, ""

        if current_count >= self.config.max_open_positions:
            return False, (
                f"Max open positions reached: {current_count} "
                f"(max: {self.config.max_open_positions})"
            )

        return True, ""

    def validate_trade(
        self,
        size_usd: float,
        capital: float,
        current_equity: float,
        peak_equity: float,
        open_position_count: int,
    ) -> TradeValidationResult:
        """
        Run all pre-trade validations.

        Args:
            size_usd: Proposed position size
            capital: Available trading capital
            current_equity: Current portfolio value
            peak_equity: Peak portfolio value
            open_position_count: Current open position count

        Returns:
            TradeValidationResult with can_trade flag and any errors
        """
        errors = []

        # Position size check
        valid, error = self.validate_position_size(size_usd, capital)
        if not valid:
            errors.append(error)

        # Daily loss check
        valid, error = self.validate_daily_loss()
        if not valid:
            errors.append(error)

        # Drawdown check
        valid, error = self.validate_drawdown(current_equity, peak_equity)
        if not valid:
            errors.append(error)

        # Open positions check
        valid, error = self.validate_open_positions(open_position_count)
        if not valid:
            errors.append(error)

        return TradeValidationResult(
            can_trade=len(errors) == 0,
            errors=errors,
        )
