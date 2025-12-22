"""Conservative low-risk trading strategy."""

from ..base import Strategy, ExitDecision, PositionContext, calculate_pnl_percent
from ....config import get_settings


class ConservativeStrategy:
    """Conservative strategy with tighter stops and quicker profits."""

    TAKE_PROFIT = 0.25  # 25%
    STOP_LOSS = -0.15   # -15%
    MIN_CONFIDENCE = 0.80  # Higher confidence required

    def __init__(self) -> None:
        self.settings = get_settings()

    @property
    def name(self) -> str:
        return "conservative"

    @property
    def description(self) -> str:
        return f"Conservative: TP {self.TAKE_PROFIT:.0%}, SL {abs(self.STOP_LOSS):.0%}"

    def should_enter(
        self,
        confidence: float,
        spread: float,
        price: float,
    ) -> bool:
        """Only accept high-confidence signals with tight spreads."""
        min_conf = max(self.MIN_CONFIDENCE, self.settings.min_confidence)
        max_spread = min(5.0, self.settings.max_spread_percent)  # Tighter spread

        return (
            confidence >= min_conf
            and spread <= max_spread
            and self.settings.min_entry_price <= price <= self.settings.max_entry_price
        )

    def should_exit(self, ctx: PositionContext) -> ExitDecision:
        """Exit quickly on profit or loss."""
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
        """Smaller position sizes for lower risk."""
        base_size = available_capital * self.settings.position_size_percent
        return base_size * 0.5 * confidence  # Half the normal size
