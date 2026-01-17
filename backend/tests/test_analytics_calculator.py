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


class TestRiskMetrics:
    """Test risk-adjusted metrics calculation."""

    def test_empty_positions(self):
        """Test with no positions."""
        calc = AnalyticsCalculator([])
        risk = calc.calculate_risk_metrics()

        assert risk.sharpe_ratio is None
        assert risk.max_drawdown == 0.0

    def test_sharpe_ratio_calculation(self):
        """Test Sharpe ratio with consistent returns."""
        # Create positions with known daily returns - all identical so std_dev = 0
        positions = [
            Position(id=i, status="closed", realized_pnl=10.0, realized_pnl_percent=2.0,
                     entry_price=0.5, size=100, opened_at=f"2025-01-{i+1:02d}T10:00:00Z",
                     closed_at=f"2025-01-{i+1:02d}T12:00:00Z")
            for i in range(10)
        ]
        calc = AnalyticsCalculator(positions)
        risk = calc.calculate_risk_metrics()

        # With constant returns (std_dev = 0), Sharpe is undefined (returns None)
        assert risk.sharpe_ratio is None

    def test_max_drawdown(self):
        """Test max drawdown calculation."""
        # Create sequence: +10, +10, -30, +5 (drawdown of 30 from peak of 20)
        positions = [
            Position(id=1, status="closed", realized_pnl=10.0, entry_price=0.5, size=100,
                     closed_at="2025-01-01T12:00:00Z"),
            Position(id=2, status="closed", realized_pnl=10.0, entry_price=0.5, size=100,
                     closed_at="2025-01-02T12:00:00Z"),
            Position(id=3, status="closed", realized_pnl=-30.0, entry_price=0.5, size=100,
                     closed_at="2025-01-03T12:00:00Z"),
            Position(id=4, status="closed", realized_pnl=5.0, entry_price=0.5, size=100,
                     closed_at="2025-01-04T12:00:00Z"),
        ]
        calc = AnalyticsCalculator(positions)
        risk = calc.calculate_risk_metrics()

        # Peak was 20, dropped to -10, drawdown = 30
        assert risk.max_drawdown == 30.0

    def test_sortino_ratio(self):
        """Test Sortino ratio only considers downside volatility."""
        positions = [
            Position(id=1, status="closed", realized_pnl=20.0, realized_pnl_percent=4.0,
                     entry_price=0.5, size=100, closed_at="2025-01-01T12:00:00Z"),
            Position(id=2, status="closed", realized_pnl=-5.0, realized_pnl_percent=-1.0,
                     entry_price=0.5, size=100, closed_at="2025-01-02T12:00:00Z"),
            Position(id=3, status="closed", realized_pnl=15.0, realized_pnl_percent=3.0,
                     entry_price=0.5, size=100, closed_at="2025-01-03T12:00:00Z"),
        ]
        calc = AnalyticsCalculator(positions)
        risk = calc.calculate_risk_metrics()

        assert risk.sortino_ratio is not None
        # Sortino should be higher than Sharpe when most returns are positive
        if risk.sharpe_ratio:
            assert risk.sortino_ratio >= risk.sharpe_ratio


class TestEfficiencyMetrics:
    """Test trading efficiency metrics."""

    def test_empty_positions(self):
        """Test with no positions."""
        calc = AnalyticsCalculator([])
        eff = calc.calculate_efficiency_metrics()

        assert eff.profit_factor is None
        assert eff.expectancy == 0.0

    def test_profit_factor(self):
        """Test profit factor calculation."""
        positions = [
            Position(id=1, status="closed", realized_pnl=30.0, entry_price=0.5, size=100),
            Position(id=2, status="closed", realized_pnl=-10.0, entry_price=0.5, size=100),
            Position(id=3, status="closed", realized_pnl=20.0, entry_price=0.5, size=100),
        ]
        calc = AnalyticsCalculator(positions)
        eff = calc.calculate_efficiency_metrics()

        # Profit factor = gross profit / gross loss = 50 / 10 = 5.0
        assert eff.profit_factor == 5.0
        # Expectancy = (win_rate * avg_win) - (loss_rate * avg_loss)
        # = (0.667 * 25) - (0.333 * 10) = 16.67 - 3.33 = 13.33
        assert eff.expectancy == pytest.approx(13.33, rel=0.01)

    def test_win_loss_streaks(self):
        """Test streak calculation."""
        positions = [
            Position(id=1, status="closed", realized_pnl=10.0, closed_at="2025-01-01T12:00:00Z"),
            Position(id=2, status="closed", realized_pnl=10.0, closed_at="2025-01-02T12:00:00Z"),
            Position(id=3, status="closed", realized_pnl=10.0, closed_at="2025-01-03T12:00:00Z"),
            Position(id=4, status="closed", realized_pnl=-5.0, closed_at="2025-01-04T12:00:00Z"),
            Position(id=5, status="closed", realized_pnl=-5.0, closed_at="2025-01-05T12:00:00Z"),
            Position(id=6, status="closed", realized_pnl=10.0, closed_at="2025-01-06T12:00:00Z"),
        ]
        calc = AnalyticsCalculator(positions)
        eff = calc.calculate_efficiency_metrics()

        assert eff.longest_win_streak == 3
        assert eff.longest_loss_streak == 2
        assert eff.current_streak == 1
        assert eff.current_streak_type == "win"

    def test_avg_hold_time(self):
        """Test average hold time calculation."""
        positions = [
            Position(id=1, status="closed", realized_pnl=10.0,
                     opened_at="2025-01-01T10:00:00Z", closed_at="2025-01-01T12:00:00Z"),  # 2 hours
            Position(id=2, status="closed", realized_pnl=10.0,
                     opened_at="2025-01-02T10:00:00Z", closed_at="2025-01-02T14:00:00Z"),  # 4 hours
        ]
        calc = AnalyticsCalculator(positions)
        eff = calc.calculate_efficiency_metrics()

        assert eff.avg_hold_time_hours == 3.0  # (2 + 4) / 2


class TestFullSummary:
    """Test full analytics summary."""

    def test_calculate_summary(self):
        """Test complete summary calculation."""
        positions = [
            Position(id=1, status="closed", realized_pnl=30.0, entry_price=0.5, size=100,
                     opened_at="2025-01-01T10:00:00Z", closed_at="2025-01-01T12:00:00Z"),
            Position(id=2, status="open", unrealized_pnl=5.0, entry_price=0.5, size=100),
        ]
        calc = AnalyticsCalculator(positions)
        summary = calc.calculate_summary()

        assert summary.basic.total_trades == 1
        assert summary.basic.total_realized_pnl == 30.0
        assert summary.total_invested > 0


class TestTimeseries:
    """Test timeseries generation."""

    def test_equity_curve_daily(self):
        """Test daily equity curve generation."""
        positions = [
            Position(id=1, status="closed", realized_pnl=10.0,
                     closed_at="2025-01-01T12:00:00Z"),
            Position(id=2, status="closed", realized_pnl=20.0,
                     closed_at="2025-01-01T14:00:00Z"),
            Position(id=3, status="closed", realized_pnl=-5.0,
                     closed_at="2025-01-02T12:00:00Z"),
        ]
        calc = AnalyticsCalculator(positions)
        series = calc.calculate_equity_timeseries(granularity="daily")

        assert len(series) == 2
        # Day 1: cumulative 30
        assert series[0].value == 30.0
        # Day 2: cumulative 25
        assert series[1].value == 25.0

    def test_drawdown_series(self):
        """Test drawdown timeseries."""
        positions = [
            Position(id=1, status="closed", realized_pnl=20.0,
                     closed_at="2025-01-01T12:00:00Z"),
            Position(id=2, status="closed", realized_pnl=-30.0,
                     closed_at="2025-01-02T12:00:00Z"),
            Position(id=3, status="closed", realized_pnl=5.0,
                     closed_at="2025-01-03T12:00:00Z"),
        ]
        calc = AnalyticsCalculator(positions)
        series = calc.calculate_drawdown_timeseries(granularity="daily")

        assert len(series) == 3
        # Day 1: no drawdown (at peak)
        assert series[0].value == 0.0
        # Day 2: drawdown of 30 (from peak 20 to -10)
        assert series[1].value == 30.0
        # Day 3: drawdown of 25 (from peak 20 to -5)
        assert series[2].value == 25.0
