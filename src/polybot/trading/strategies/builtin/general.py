"""General balanced trading strategy."""

from ..base import Strategy, ExitDecision, PositionContext, calculate_pnl_percent
from ....config import get_settings


class GeneralStrategy:
    """Balanced strategy with 50% take profit and 25% stop loss."""

    TAKE_PROFIT = 0.50  # 50%
    STOP_LOSS = -0.25   # -25%

    def __init__(self) -> None:
        self.settings = get_settings()

    @property
    def name(self) -> str:
        return "general"

    @property
    def description(self) -> str:
        return f"Balanced: TP {self.TAKE_PROFIT:.0%}, SL {abs(self.STOP_LOSS):.0%}"

    def should_enter(
        self,
        confidence: float,
        spread: float,
        price: float,
    ) -> bool:
        """Accept signals that meet basic criteria."""
        return (
            confidence >= self.settings.min_confidence
            and spread <= self.settings.max_spread_percent
            and self.settings.min_entry_price <= price <= self.settings.max_entry_price
        )

    def should_exit(self, ctx: PositionContext) -> ExitDecision:
        """Exit on take profit or stop loss."""
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
        """Calculate position size based on confidence."""
        base_size = available_capital * self.settings.position_size_percent
        return base_size * confidence  # Scale by confidence
