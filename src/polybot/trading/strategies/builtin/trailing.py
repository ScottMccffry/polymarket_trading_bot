"""Trailing stop strategy."""

from ..base import Strategy, ExitDecision, PositionContext, calculate_pnl_percent
from ....config import get_settings


class TrailingStopStrategy:
    """Strategy that trails stops from peak price."""

    TRAILING_STOP = 0.20  # 20% from peak
    INITIAL_STOP = -0.25  # -25% initial stop loss

    def __init__(self) -> None:
        self.settings = get_settings()

    @property
    def name(self) -> str:
        return "trailing_stop"

    @property
    def description(self) -> str:
        return f"Trailing: {self.TRAILING_STOP:.0%} from peak, initial SL {abs(self.INITIAL_STOP):.0%}"

    def should_enter(
        self,
        confidence: float,
        spread: float,
        price: float,
    ) -> bool:
        """Standard entry criteria."""
        return (
            confidence >= self.settings.min_confidence
            and spread <= self.settings.max_spread_percent
            and self.settings.min_entry_price <= price <= self.settings.max_entry_price
        )

    def should_exit(self, ctx: PositionContext) -> ExitDecision:
        """Exit based on trailing stop from peak or initial stop loss."""
        pnl_pct = calculate_pnl_percent(ctx.entry_price, ctx.current_price, ctx.side)

        # Initial stop loss
        if pnl_pct <= self.INITIAL_STOP:
            return ExitDecision(
                should_exit=True,
                reason="stop_loss",
                exit_percent=1.0,
            )

        # Trailing stop from peak
        if ctx.peak_price is not None:
            peak_pnl = calculate_pnl_percent(ctx.entry_price, ctx.peak_price, ctx.side)

            # Only trail if we've been profitable
            if peak_pnl > 0:
                drop_from_peak = peak_pnl - pnl_pct
                if drop_from_peak >= self.TRAILING_STOP:
                    return ExitDecision(
                        should_exit=True,
                        reason="trailing_stop",
                        exit_percent=1.0,
                    )

        return ExitDecision(should_exit=False, reason="", exit_percent=0.0)

    def calculate_size(
        self,
        available_capital: float,
        confidence: float,
    ) -> float:
        """Standard position size."""
        base_size = available_capital * self.settings.position_size_percent
        return base_size * confidence
