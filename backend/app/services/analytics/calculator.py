"""Analytics calculator for computing trading metrics."""
from typing import Sequence

from ...models.position import Position
from ...models.analytics import (
    BasicMetrics,
    RiskMetrics,
    EfficiencyMetrics,
    AnalyticsSummary,
)


class AnalyticsCalculator:
    """Calculate trading analytics from positions."""

    def __init__(self, positions: Sequence[Position]):
        self.positions = list(positions)
        self.closed = [p for p in self.positions if p.status == "closed"]
        self.open = [p for p in self.positions if p.status == "open"]
        self.wins = [p for p in self.closed if (p.realized_pnl or 0) > 0]
        self.losses = [p for p in self.closed if (p.realized_pnl or 0) <= 0]

    def calculate_basic_metrics(self) -> BasicMetrics:
        """Calculate basic PnL metrics."""
        total_realized = sum(p.realized_pnl or 0 for p in self.closed)
        total_unrealized = sum(p.unrealized_pnl or 0 for p in self.open)

        # Calculate invested amounts for percentages
        closed_invested = sum((p.entry_price or 0) * (p.size or 0) for p in self.closed)
        open_invested = sum((p.entry_price or 0) * (p.size or 0) for p in self.open)

        total_realized_pct = (total_realized / closed_invested * 100) if closed_invested > 0 else 0
        total_unrealized_pct = (total_unrealized / open_invested * 100) if open_invested > 0 else 0

        # Win/loss averages
        avg_win = (sum(p.realized_pnl or 0 for p in self.wins) / len(self.wins)) if self.wins else 0
        avg_loss = (abs(sum(p.realized_pnl or 0 for p in self.losses)) / len(self.losses)) if self.losses else 0

        # Best/worst
        pnls = [p.realized_pnl or 0 for p in self.closed]
        best = max(pnls) if pnls else 0
        worst = min(pnls) if pnls else 0

        # Win rate
        win_rate = (len(self.wins) / len(self.closed) * 100) if self.closed else 0

        return BasicMetrics(
            total_realized_pnl=round(total_realized, 2),
            total_realized_pnl_percent=round(total_realized_pct, 2),
            total_unrealized_pnl=round(total_unrealized, 2),
            total_unrealized_pnl_percent=round(total_unrealized_pct, 2),
            total_trades=len(self.closed),
            open_trades=len(self.open),
            closed_trades=len(self.closed),
            wins=len(self.wins),
            losses=len(self.losses),
            win_rate=round(win_rate, 2),
            avg_win=round(avg_win, 2),
            avg_loss=round(avg_loss, 2),
            best_trade=round(best, 2),
            worst_trade=round(worst, 2),
        )
