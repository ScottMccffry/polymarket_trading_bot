"""Analytics calculator for computing trading metrics."""
import math
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

    def calculate_risk_metrics(self) -> RiskMetrics:
        """Calculate risk-adjusted metrics."""
        if not self.closed:
            return RiskMetrics(
                sharpe_ratio=None,
                sortino_ratio=None,
                max_drawdown=0.0,
                max_drawdown_percent=0.0,
                current_drawdown=0.0,
                current_drawdown_percent=0.0,
                risk_reward_ratio=None,
                calmar_ratio=None,
            )

        # Get returns sorted by close time
        sorted_closed = sorted(
            self.closed,
            key=lambda p: p.closed_at or ""
        )
        returns = [p.realized_pnl_percent or 0 for p in sorted_closed]
        pnls = [p.realized_pnl or 0 for p in sorted_closed]

        # Sharpe ratio (annualized, assuming 252 trading days)
        sharpe = self._calculate_sharpe(returns)

        # Sortino ratio (only downside deviation)
        sortino = self._calculate_sortino(returns)

        # Max drawdown
        max_dd, max_dd_pct, curr_dd, curr_dd_pct = self._calculate_drawdown(pnls)

        # Risk/reward ratio
        basic = self.calculate_basic_metrics()
        risk_reward = (basic.avg_win / basic.avg_loss) if basic.avg_loss > 0 else None

        # Calmar ratio (return / max drawdown)
        total_invested = sum((p.entry_price or 0) * (p.size or 0) for p in self.closed)
        total_return_pct = (sum(pnls) / total_invested * 100) if total_invested > 0 else 0
        calmar = (total_return_pct / max_dd_pct) if max_dd_pct > 0 else None

        return RiskMetrics(
            sharpe_ratio=round(sharpe, 2) if sharpe else None,
            sortino_ratio=round(sortino, 2) if sortino else None,
            max_drawdown=round(max_dd, 2),
            max_drawdown_percent=round(max_dd_pct, 2),
            current_drawdown=round(curr_dd, 2),
            current_drawdown_percent=round(curr_dd_pct, 2),
            risk_reward_ratio=round(risk_reward, 2) if risk_reward else None,
            calmar_ratio=round(calmar, 2) if calmar else None,
        )

    def _calculate_sharpe(self, returns: list[float], risk_free_rate: float = 0) -> float | None:
        """Calculate annualized Sharpe ratio."""
        if len(returns) < 2:
            return None

        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / (len(returns) - 1)
        std_dev = math.sqrt(variance) if variance > 0 else 0

        if std_dev == 0:
            return None

        # Annualize (assuming daily returns, 252 trading days)
        sharpe = (mean_return - risk_free_rate) / std_dev * math.sqrt(252)
        return sharpe

    def _calculate_sortino(self, returns: list[float], risk_free_rate: float = 0) -> float | None:
        """Calculate Sortino ratio (uses downside deviation)."""
        if len(returns) < 2:
            return None

        mean_return = sum(returns) / len(returns)

        # Only negative returns for downside deviation
        negative_returns = [r for r in returns if r < 0]
        if not negative_returns:
            return None

        downside_variance = sum(r ** 2 for r in negative_returns) / len(negative_returns)
        downside_dev = math.sqrt(downside_variance)

        if downside_dev == 0:
            return None

        sortino = (mean_return - risk_free_rate) / downside_dev * math.sqrt(252)
        return sortino

    def _calculate_drawdown(self, pnls: list[float]) -> tuple[float, float, float, float]:
        """Calculate max and current drawdown."""
        if not pnls:
            return 0.0, 0.0, 0.0, 0.0

        cumulative = 0.0
        peak = 0.0
        max_drawdown = 0.0

        total_invested = sum((p.entry_price or 0) * (p.size or 0) for p in self.closed)

        for pnl in pnls:
            cumulative += pnl
            if cumulative > peak:
                peak = cumulative
            drawdown = peak - cumulative
            if drawdown > max_drawdown:
                max_drawdown = drawdown

        current_drawdown = peak - cumulative

        # Calculate percentages
        max_dd_pct = (max_drawdown / total_invested * 100) if total_invested > 0 else 0
        curr_dd_pct = (current_drawdown / total_invested * 100) if total_invested > 0 else 0

        return max_drawdown, max_dd_pct, current_drawdown, curr_dd_pct
