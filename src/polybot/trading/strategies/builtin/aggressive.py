"""Aggressive high-risk/high-reward trading strategy."""

from ..base import Strategy, ExitDecision, PositionContext, calculate_pnl_percent
from ....config import get_settings


class AggressiveStrategy:
    """Aggressive strategy with wide stops and big profit targets."""

    TAKE_PROFIT = 1.00  # 100%
    STOP_LOSS = -0.40   # -40%
    MIN_CONFIDENCE = 0.70  # Lower confidence accepted

    def __init__(self) -> None:
        self.settings = get_settings()

    @property
    def name(self) -> str:
        return "aggressive"

    @property
    def description(self) -> str:
        return f"Aggressive: TP {self.TAKE_PROFIT:.0%}, SL {abs(self.STOP_LOSS):.0%}"

    def should_enter(
        self,
        confidence: float,
        spread: float,
        price: float,
    ) -> bool:
        """Accept signals with lower confidence threshold."""
        min_conf = min(self.MIN_CONFIDENCE, self.settings.min_confidence)

        return (
            confidence >= min_conf
            and spread <= self.settings.max_spread_percent
            and self.settings.min_entry_price <= price <= self.settings.max_entry_price
        )

    def should_exit(self, ctx: PositionContext) -> ExitDecision:
        """Exit on big profits or wide stops."""
        pnl_pct = calculate_pnl_percent(ctx.entry_price, ctx.current_price, ctx.side)

        if pnl_pct >= self.TAKE_PROFIT:
            return ExitDecision(
                should_exit=True,
                reason="take_profit",
                exit_percent=1.0,
            )

        if pnl_pct <= self.STOP_LOSS:
            return ExitDecision(
                should_exit=True,
                reason="stop_loss",
                exit_percent=1.0,
            )

        return ExitDecision(should_exit=False, reason="", exit_percent=0.0)

    def calculate_size(
        self,
        available_capital: float,
        confidence: float,
    ) -> float:
        """Larger position sizes for higher risk."""
        base_size = available_capital * self.settings.position_size_percent
        return base_size * 1.5 * confidence  # 1.5x normal size
