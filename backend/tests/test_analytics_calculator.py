"""Tests for analytics calculator."""
import pytest

from app.models.position import Position
from app.services.analytics.calculator import AnalyticsCalculator


class TestBasicMetrics:
    """Test basic PnL metrics calculation."""

    def test_empty_positions(self):
        """Test with no positions."""
        calc = AnalyticsCalculator([])
        basic = calc.calculate_basic_metrics()

        assert basic.total_trades == 0
        assert basic.win_rate == 0.0
        assert basic.total_realized_pnl == 0.0

    def test_single_winning_trade(self):
        """Test with one winning closed trade."""
        pos = Position(
            id=1,
            status="closed",
            entry_price=0.5,
            exit_price=0.7,
            size=100.0,
            realized_pnl=20.0,
            realized_pnl_percent=40.0,
            opened_at="2025-01-01T10:00:00Z",
            closed_at="2025-01-01T12:00:00Z",
        )
        calc = AnalyticsCalculator([pos])
        basic = calc.calculate_basic_metrics()

        assert basic.total_trades == 1
        assert basic.closed_trades == 1
        assert basic.wins == 1
        assert basic.losses == 0
        assert basic.win_rate == 100.0
        assert basic.total_realized_pnl == 20.0
        assert basic.avg_win == 20.0
        assert basic.best_trade == 20.0

    def test_mixed_trades(self):
        """Test with mix of wins and losses."""
        positions = [
            Position(id=1, status="closed", realized_pnl=30.0, entry_price=0.5, size=100),
            Position(id=2, status="closed", realized_pnl=-10.0, entry_price=0.5, size=100),
            Position(id=3, status="closed", realized_pnl=20.0, entry_price=0.5, size=100),
            Position(id=4, status="open", unrealized_pnl=5.0, entry_price=0.5, size=100),
        ]
        calc = AnalyticsCalculator(positions)
        basic = calc.calculate_basic_metrics()

        assert basic.total_trades == 3  # closed only
        assert basic.open_trades == 1
        assert basic.wins == 2
        assert basic.losses == 1
        assert basic.win_rate == pytest.approx(66.67, rel=0.01)
        assert basic.total_realized_pnl == 40.0
        assert basic.total_unrealized_pnl == 5.0
        assert basic.avg_win == 25.0  # (30 + 20) / 2
        assert basic.avg_loss == 10.0
        assert basic.best_trade == 30.0
        assert basic.worst_trade == -10.0

    def test_breakeven_trade(self):
        """Test that breakeven (zero PnL) trades are counted as losses.

        Current behavior: A trade with realized_pnl=0 is classified as a loss
        because the condition for wins is `realized_pnl > 0` (strictly greater).
        This documents the expected behavior.
        """
        pos = Position(
            id=1,
            status="closed",
            entry_price=0.5,
            exit_price=0.5,
            size=100.0,
            realized_pnl=0.0,
            realized_pnl_percent=0.0,
        )
        calc = AnalyticsCalculator([pos])
        basic = calc.calculate_basic_metrics()

        # Breakeven trade counts as a loss (pnl <= 0)
        assert basic.wins == 0
        assert basic.losses == 1
        assert basic.win_rate == 0.0
        assert basic.total_realized_pnl == 0.0
        assert basic.avg_loss == 0.0  # avg of [0] = 0

    def test_percentage_calculations(self):
        """Test that PnL percentages are calculated correctly.

        Percentage = (PnL / Invested Amount) * 100
        Invested Amount = entry_price * size
        """
        positions = [
            # Closed position: invested $50 (0.5 * 100), made $10 profit -> 20%
            Position(
                id=1,
                status="closed",
                entry_price=0.5,
                size=100.0,
                realized_pnl=10.0,
            ),
            # Closed position: invested $25 (0.25 * 100), lost $5 -> -20%
            Position(
                id=2,
                status="closed",
                entry_price=0.25,
                size=100.0,
                realized_pnl=-5.0,
            ),
            # Open position: invested $40 (0.4 * 100), unrealized $8 -> 20%
            Position(
                id=3,
                status="open",
                entry_price=0.4,
                size=100.0,
                unrealized_pnl=8.0,
            ),
        ]
        calc = AnalyticsCalculator(positions)
        basic = calc.calculate_basic_metrics()

        # Total realized: $10 - $5 = $5
        # Total closed invested: $50 + $25 = $75
        # Realized percent: ($5 / $75) * 100 = 6.67%
        assert basic.total_realized_pnl == 5.0
        assert basic.total_realized_pnl_percent == pytest.approx(6.67, rel=0.01)

        # Total unrealized: $8
        # Total open invested: $40
        # Unrealized percent: ($8 / $40) * 100 = 20%
        assert basic.total_unrealized_pnl == 8.0
        assert basic.total_unrealized_pnl_percent == 20.0
