# Statistics & Analytics Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a comprehensive real-time analytics dashboard with advanced trading metrics, flexible filtering, and live WebSocket updates.

**Architecture:** Backend analytics service computes metrics on-demand from positions table. WebSocket broadcasts updates on position changes. Frontend dashboard uses Lightweight Charts for financial visualizations and ShadCN for UI components.

**Tech Stack:** FastAPI, SQLAlchemy, WebSocket, Next.js, TypeScript, Lightweight Charts, ShadCN, Tailwind CSS

---

## Task 1: Backend Pydantic Models for Analytics

**Files:**
- Create: `backend/app/models/analytics.py`

**Step 1: Create the analytics response models**

```python
"""Pydantic models for analytics responses."""
from pydantic import BaseModel
from typing import Literal


class BasicMetrics(BaseModel):
    """Basic PnL metrics."""
    total_realized_pnl: float
    total_realized_pnl_percent: float
    total_unrealized_pnl: float
    total_unrealized_pnl_percent: float
    total_trades: int
    open_trades: int
    closed_trades: int
    wins: int
    losses: int
    win_rate: float
    avg_win: float
    avg_loss: float
    best_trade: float
    worst_trade: float


class RiskMetrics(BaseModel):
    """Risk-adjusted metrics."""
    sharpe_ratio: float | None
    sortino_ratio: float | None
    max_drawdown: float
    max_drawdown_percent: float
    current_drawdown: float
    current_drawdown_percent: float
    risk_reward_ratio: float | None
    calmar_ratio: float | None


class EfficiencyMetrics(BaseModel):
    """Trading efficiency metrics."""
    profit_factor: float | None
    expectancy: float
    avg_hold_time_hours: float | None
    trades_per_day: float
    longest_win_streak: int
    longest_loss_streak: int
    current_streak: int
    current_streak_type: Literal["win", "loss", "none"]


class AnalyticsSummary(BaseModel):
    """Complete analytics summary."""
    basic: BasicMetrics
    risk: RiskMetrics
    efficiency: EfficiencyMetrics
    total_invested: float
    filters_applied: dict


class GroupedAnalytics(BaseModel):
    """Analytics grouped by a dimension."""
    group_key: str
    group_value: str
    summary: AnalyticsSummary


class AnalyticsSummaryResponse(BaseModel):
    """Response for /api/analytics/summary endpoint."""
    totals: AnalyticsSummary
    groups: list[GroupedAnalytics]


class TimeseriesPoint(BaseModel):
    """Single point in a timeseries."""
    timestamp: str
    value: float
    group: str | None = None


class TimeseriesResponse(BaseModel):
    """Response for /api/analytics/timeseries endpoint."""
    metric: str
    granularity: str
    data: list[TimeseriesPoint]


class HeatmapCell(BaseModel):
    """Single cell in heatmap."""
    x: str  # e.g., "Monday" or "0" (hour)
    y: str | None = None  # optional second dimension
    value: float
    count: int


class HeatmapResponse(BaseModel):
    """Response for /api/analytics/heatmap endpoint."""
    dimension: str
    metric: str
    cells: list[HeatmapCell]


class TradeRecord(BaseModel):
    """Single trade for trades list."""
    id: int
    market_question: str | None
    side: str | None
    entry_price: float | None
    exit_price: float | None
    size: float | None
    realized_pnl: float | None
    realized_pnl_percent: float | None
    status: str
    strategy_name: str | None
    source: str | None
    trading_mode: str | None
    opened_at: str | None
    closed_at: str | None
    hold_time_hours: float | None


class TradesResponse(BaseModel):
    """Response for /api/analytics/trades endpoint."""
    trades: list[TradeRecord]
    total_count: int
    limit: int
    offset: int
```

**Step 2: Verify file created correctly**

Run: `python -c "from app.models.analytics import AnalyticsSummaryResponse; print('OK')"`
Expected: OK

**Step 3: Commit**

```bash
git add backend/app/models/analytics.py
git commit -m "feat(analytics): add Pydantic response models"
```

---

## Task 2: Backend Analytics Calculator - Basic Metrics

**Files:**
- Create: `backend/app/services/analytics/__init__.py`
- Create: `backend/app/services/analytics/calculator.py`
- Create: `backend/tests/test_analytics_calculator.py`

**Step 1: Create the analytics service directory and init**

```python
# backend/app/services/analytics/__init__.py
"""Analytics service for computing trading metrics."""
from .calculator import AnalyticsCalculator

__all__ = ["AnalyticsCalculator"]
```

**Step 2: Write failing test for basic metrics**

```python
# backend/tests/test_analytics_calculator.py
"""Tests for analytics calculator."""
import pytest
from datetime import datetime, UTC, timedelta

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
```

**Step 3: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_analytics_calculator.py -v`
Expected: FAIL (module not found)

**Step 4: Implement basic metrics calculator**

```python
# backend/app/services/analytics/calculator.py
"""Analytics calculator for computing trading metrics."""
from dataclasses import dataclass
from datetime import datetime
from typing import Sequence
import math

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
```

**Step 5: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_analytics_calculator.py::TestBasicMetrics -v`
Expected: PASS (3 tests)

**Step 6: Commit**

```bash
git add backend/app/services/analytics/ backend/tests/test_analytics_calculator.py
git commit -m "feat(analytics): add basic metrics calculator with tests"
```

---

## Task 3: Analytics Calculator - Risk Metrics

**Files:**
- Modify: `backend/app/services/analytics/calculator.py`
- Modify: `backend/tests/test_analytics_calculator.py`

**Step 1: Write failing tests for risk metrics**

Add to `backend/tests/test_analytics_calculator.py`:

```python
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
        # Create positions with known daily returns
        positions = [
            Position(id=i, status="closed", realized_pnl=10.0, realized_pnl_percent=2.0,
                     entry_price=0.5, size=100, opened_at=f"2025-01-{i+1:02d}T10:00:00Z",
                     closed_at=f"2025-01-{i+1:02d}T12:00:00Z")
            for i in range(10)
        ]
        calc = AnalyticsCalculator(positions)
        risk = calc.calculate_risk_metrics()

        # With constant positive returns, Sharpe should be very high (low std dev)
        assert risk.sharpe_ratio is not None
        assert risk.sharpe_ratio > 0

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
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_analytics_calculator.py::TestRiskMetrics -v`
Expected: FAIL (method not found)

**Step 3: Implement risk metrics**

Add to `AnalyticsCalculator` class in `backend/app/services/analytics/calculator.py`:

```python
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
        total_return_pct = sum(returns)
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
            return None if mean_return == 0 else float('inf') if mean_return > 0 else float('-inf')

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
            return float('inf') if mean_return > 0 else None

        downside_variance = sum(r ** 2 for r in negative_returns) / len(returns)
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
```

**Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_analytics_calculator.py::TestRiskMetrics -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/services/analytics/calculator.py backend/tests/test_analytics_calculator.py
git commit -m "feat(analytics): add risk metrics (Sharpe, Sortino, drawdown)"
```

---

## Task 4: Analytics Calculator - Efficiency Metrics

**Files:**
- Modify: `backend/app/services/analytics/calculator.py`
- Modify: `backend/tests/test_analytics_calculator.py`

**Step 1: Write failing tests for efficiency metrics**

Add to `backend/tests/test_analytics_calculator.py`:

```python
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
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_analytics_calculator.py::TestEfficiencyMetrics -v`
Expected: FAIL

**Step 3: Implement efficiency metrics**

Add to `AnalyticsCalculator` class:

```python
    def calculate_efficiency_metrics(self) -> EfficiencyMetrics:
        """Calculate trading efficiency metrics."""
        if not self.closed:
            return EfficiencyMetrics(
                profit_factor=None,
                expectancy=0.0,
                avg_hold_time_hours=None,
                trades_per_day=0.0,
                longest_win_streak=0,
                longest_loss_streak=0,
                current_streak=0,
                current_streak_type="none",
            )

        # Profit factor
        gross_profit = sum(p.realized_pnl or 0 for p in self.wins)
        gross_loss = abs(sum(p.realized_pnl or 0 for p in self.losses))
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else None

        # Expectancy
        basic = self.calculate_basic_metrics()
        win_rate = basic.win_rate / 100
        loss_rate = 1 - win_rate
        expectancy = (win_rate * basic.avg_win) - (loss_rate * basic.avg_loss)

        # Average hold time
        hold_times = []
        for p in self.closed:
            if p.opened_at and p.closed_at:
                try:
                    opened = datetime.fromisoformat(p.opened_at.replace("Z", "+00:00"))
                    closed = datetime.fromisoformat(p.closed_at.replace("Z", "+00:00"))
                    hours = (closed - opened).total_seconds() / 3600
                    hold_times.append(hours)
                except (ValueError, TypeError):
                    pass
        avg_hold = (sum(hold_times) / len(hold_times)) if hold_times else None

        # Trades per day
        trades_per_day = self._calculate_trades_per_day()

        # Streaks
        win_streak, loss_streak, current, current_type = self._calculate_streaks()

        return EfficiencyMetrics(
            profit_factor=round(profit_factor, 2) if profit_factor else None,
            expectancy=round(expectancy, 2),
            avg_hold_time_hours=round(avg_hold, 2) if avg_hold else None,
            trades_per_day=round(trades_per_day, 2),
            longest_win_streak=win_streak,
            longest_loss_streak=loss_streak,
            current_streak=current,
            current_streak_type=current_type,
        )

    def _calculate_trades_per_day(self) -> float:
        """Calculate average trades per day."""
        if not self.closed:
            return 0.0

        dates = set()
        for p in self.closed:
            if p.closed_at:
                try:
                    date = datetime.fromisoformat(p.closed_at.replace("Z", "+00:00")).date()
                    dates.add(date)
                except (ValueError, TypeError):
                    pass

        if not dates:
            return 0.0

        return len(self.closed) / len(dates)

    def _calculate_streaks(self) -> tuple[int, int, int, str]:
        """Calculate win/loss streaks."""
        sorted_closed = sorted(self.closed, key=lambda p: p.closed_at or "")

        if not sorted_closed:
            return 0, 0, 0, "none"

        longest_win = 0
        longest_loss = 0
        current_win = 0
        current_loss = 0

        for p in sorted_closed:
            if (p.realized_pnl or 0) > 0:
                current_win += 1
                current_loss = 0
                longest_win = max(longest_win, current_win)
            else:
                current_loss += 1
                current_win = 0
                longest_loss = max(longest_loss, current_loss)

        # Current streak
        if current_win > 0:
            return longest_win, longest_loss, current_win, "win"
        elif current_loss > 0:
            return longest_win, longest_loss, current_loss, "loss"
        return longest_win, longest_loss, 0, "none"
```

**Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_analytics_calculator.py::TestEfficiencyMetrics -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/services/analytics/calculator.py backend/tests/test_analytics_calculator.py
git commit -m "feat(analytics): add efficiency metrics (profit factor, streaks, hold time)"
```

---

## Task 5: Analytics Calculator - Full Summary & Timeseries

**Files:**
- Modify: `backend/app/services/analytics/calculator.py`
- Modify: `backend/tests/test_analytics_calculator.py`

**Step 1: Write failing tests**

Add to `backend/tests/test_analytics_calculator.py`:

```python
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
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_analytics_calculator.py::TestFullSummary -v`
Expected: FAIL

**Step 3: Implement summary and timeseries**

Add to `AnalyticsCalculator` class:

```python
    def calculate_summary(self, filters_applied: dict | None = None) -> AnalyticsSummary:
        """Calculate complete analytics summary."""
        basic = self.calculate_basic_metrics()
        risk = self.calculate_risk_metrics()
        efficiency = self.calculate_efficiency_metrics()

        total_invested = sum((p.entry_price or 0) * (p.size or 0) for p in self.positions)

        return AnalyticsSummary(
            basic=basic,
            risk=risk,
            efficiency=efficiency,
            total_invested=round(total_invested, 2),
            filters_applied=filters_applied or {},
        )

    def calculate_equity_timeseries(
        self,
        granularity: str = "daily",
        group_by: str | None = None
    ) -> list:
        """Calculate cumulative equity timeseries."""
        from ...models.analytics import TimeseriesPoint

        if not self.closed:
            return []

        sorted_closed = sorted(self.closed, key=lambda p: p.closed_at or "")

        # Bucket by granularity
        buckets = self._bucket_by_time(sorted_closed, granularity)

        # Calculate cumulative
        cumulative = 0.0
        points = []
        for timestamp, positions in buckets.items():
            daily_pnl = sum(p.realized_pnl or 0 for p in positions)
            cumulative += daily_pnl
            points.append(TimeseriesPoint(
                timestamp=timestamp,
                value=round(cumulative, 2),
                group=None,
            ))

        return points

    def calculate_drawdown_timeseries(
        self,
        granularity: str = "daily"
    ) -> list:
        """Calculate drawdown timeseries."""
        from ...models.analytics import TimeseriesPoint

        if not self.closed:
            return []

        sorted_closed = sorted(self.closed, key=lambda p: p.closed_at or "")
        buckets = self._bucket_by_time(sorted_closed, granularity)

        cumulative = 0.0
        peak = 0.0
        points = []

        for timestamp, positions in buckets.items():
            daily_pnl = sum(p.realized_pnl or 0 for p in positions)
            cumulative += daily_pnl
            if cumulative > peak:
                peak = cumulative
            drawdown = peak - cumulative
            points.append(TimeseriesPoint(
                timestamp=timestamp,
                value=round(drawdown, 2),
                group=None,
            ))

        return points

    def _bucket_by_time(
        self,
        positions: list,
        granularity: str
    ) -> dict[str, list]:
        """Bucket positions by time granularity."""
        from collections import OrderedDict

        buckets: dict[str, list] = OrderedDict()

        for p in positions:
            if not p.closed_at:
                continue

            try:
                dt = datetime.fromisoformat(p.closed_at.replace("Z", "+00:00"))

                if granularity == "daily":
                    key = dt.strftime("%Y-%m-%d")
                elif granularity == "weekly":
                    # ISO week
                    key = dt.strftime("%Y-W%W")
                elif granularity == "monthly":
                    key = dt.strftime("%Y-%m")
                else:
                    key = dt.strftime("%Y-%m-%d")

                if key not in buckets:
                    buckets[key] = []
                buckets[key].append(p)
            except (ValueError, TypeError):
                pass

        return buckets
```

**Step 4: Run all tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_analytics_calculator.py -v`
Expected: PASS (all tests)

**Step 5: Commit**

```bash
git add backend/app/services/analytics/calculator.py backend/tests/test_analytics_calculator.py
git commit -m "feat(analytics): add summary and timeseries calculations"
```

---

## Task 6: Analytics Filtering Service

**Files:**
- Create: `backend/app/services/analytics/filters.py`
- Modify: `backend/tests/test_analytics_calculator.py`

**Step 1: Write failing test**

Add to `backend/tests/test_analytics_calculator.py`:

```python
from app.services.analytics.filters import AnalyticsFilter


class TestFiltering:
    """Test position filtering."""

    def test_filter_by_trading_mode(self):
        """Test filtering by trading mode."""
        positions = [
            Position(id=1, trading_mode="live", status="closed", realized_pnl=10.0),
            Position(id=2, trading_mode="paper", status="closed", realized_pnl=20.0),
            Position(id=3, trading_mode="live", status="closed", realized_pnl=30.0),
        ]

        filtered = AnalyticsFilter.apply(positions, trading_mode="live")
        assert len(filtered) == 2
        assert all(p.trading_mode == "live" for p in filtered)

    def test_filter_by_date_range(self):
        """Test filtering by date range."""
        positions = [
            Position(id=1, status="closed", realized_pnl=10.0, closed_at="2025-01-01T12:00:00Z"),
            Position(id=2, status="closed", realized_pnl=20.0, closed_at="2025-01-15T12:00:00Z"),
            Position(id=3, status="closed", realized_pnl=30.0, closed_at="2025-01-30T12:00:00Z"),
        ]

        filtered = AnalyticsFilter.apply(
            positions,
            start_date="2025-01-10",
            end_date="2025-01-20"
        )
        assert len(filtered) == 1
        assert filtered[0].id == 2

    def test_filter_by_strategy(self):
        """Test filtering by strategy."""
        positions = [
            Position(id=1, strategy_name="Alpha", status="closed", realized_pnl=10.0),
            Position(id=2, strategy_name="Beta", status="closed", realized_pnl=20.0),
            Position(id=3, strategy_name="Alpha", status="closed", realized_pnl=30.0),
        ]

        filtered = AnalyticsFilter.apply(positions, strategy_name="Alpha")
        assert len(filtered) == 2

    def test_group_by_strategy(self):
        """Test grouping by strategy."""
        positions = [
            Position(id=1, strategy_name="Alpha", status="closed", realized_pnl=10.0),
            Position(id=2, strategy_name="Beta", status="closed", realized_pnl=20.0),
            Position(id=3, strategy_name="Alpha", status="closed", realized_pnl=30.0),
        ]

        groups = AnalyticsFilter.group_by(positions, "strategy_name")
        assert len(groups) == 2
        assert "Alpha" in groups
        assert "Beta" in groups
        assert len(groups["Alpha"]) == 2
        assert len(groups["Beta"]) == 1
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_analytics_calculator.py::TestFiltering -v`
Expected: FAIL

**Step 3: Implement filters**

```python
# backend/app/services/analytics/filters.py
"""Filtering and grouping utilities for analytics."""
from datetime import datetime
from typing import Sequence
from collections import defaultdict

from ...models.position import Position


class AnalyticsFilter:
    """Filter and group positions for analytics."""

    @staticmethod
    def apply(
        positions: Sequence[Position],
        trading_mode: str | None = None,
        status: str | None = None,
        strategy_name: str | None = None,
        strategy_id: int | None = None,
        source: str | None = None,
        side: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> list[Position]:
        """Apply filters to positions."""
        result = list(positions)

        if trading_mode and trading_mode != "all":
            result = [p for p in result if p.trading_mode == trading_mode]

        if status and status != "all":
            result = [p for p in result if p.status == status]

        if strategy_name:
            result = [p for p in result if p.strategy_name == strategy_name]

        if strategy_id:
            result = [p for p in result if p.strategy_id == strategy_id]

        if source:
            result = [p for p in result if p.source == source]

        if side:
            result = [p for p in result if p.side == side]

        if start_date:
            start_dt = datetime.fromisoformat(start_date)
            result = [
                p for p in result
                if p.closed_at and datetime.fromisoformat(p.closed_at.replace("Z", "+00:00")).date() >= start_dt.date()
                or p.opened_at and datetime.fromisoformat(p.opened_at.replace("Z", "+00:00")).date() >= start_dt.date()
            ]

        if end_date:
            end_dt = datetime.fromisoformat(end_date)
            result = [
                p for p in result
                if p.closed_at and datetime.fromisoformat(p.closed_at.replace("Z", "+00:00")).date() <= end_dt.date()
                or p.opened_at and datetime.fromisoformat(p.opened_at.replace("Z", "+00:00")).date() <= end_dt.date()
            ]

        return result

    @staticmethod
    def group_by(
        positions: Sequence[Position],
        field: str
    ) -> dict[str, list[Position]]:
        """Group positions by a field value."""
        groups: dict[str, list[Position]] = defaultdict(list)

        for p in positions:
            value = getattr(p, field, None)
            key = str(value) if value is not None else "Unknown"
            groups[key].append(p)

        return dict(groups)

    @staticmethod
    def get_filter_options(positions: Sequence[Position]) -> dict[str, list[str]]:
        """Get available filter options from positions."""
        strategies = set()
        sources = set()
        modes = set()

        for p in positions:
            if p.strategy_name:
                strategies.add(p.strategy_name)
            if p.source:
                sources.add(p.source)
            if p.trading_mode:
                modes.add(p.trading_mode)

        return {
            "strategies": sorted(strategies),
            "sources": sorted(sources),
            "trading_modes": sorted(modes),
        }
```

**Step 4: Update __init__.py**

```python
# backend/app/services/analytics/__init__.py
"""Analytics service for computing trading metrics."""
from .calculator import AnalyticsCalculator
from .filters import AnalyticsFilter

__all__ = ["AnalyticsCalculator", "AnalyticsFilter"]
```

**Step 5: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_analytics_calculator.py::TestFiltering -v`
Expected: PASS

**Step 6: Commit**

```bash
git add backend/app/services/analytics/
git commit -m "feat(analytics): add filtering and grouping service"
```

---

## Task 7: Backend Analytics API Routes

**Files:**
- Create: `backend/app/routes/analytics.py`
- Modify: `backend/app/routes/__init__.py`
- Create: `backend/tests/test_analytics_routes.py`

**Step 1: Write failing test for summary endpoint**

```python
# backend/tests/test_analytics_routes.py
"""Tests for analytics API routes."""
import pytest
from datetime import datetime, UTC

from app.models.position import Position


class TestAnalyticsSummary:
    """Test /api/analytics/summary endpoint."""

    @pytest.mark.asyncio
    async def test_summary_empty(self, client):
        """Test summary with no positions."""
        response = await client.get("/api/analytics/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["totals"]["basic"]["total_trades"] == 0

    @pytest.mark.asyncio
    async def test_summary_with_positions(self, client, db_session):
        """Test summary with positions."""
        positions = [
            Position(
                id=1, status="closed", realized_pnl=30.0, realized_pnl_percent=10.0,
                entry_price=0.5, size=100, trading_mode="live",
                strategy_name="Alpha", source="telegram",
                opened_at="2025-01-01T10:00:00Z", closed_at="2025-01-01T12:00:00Z"
            ),
            Position(
                id=2, status="closed", realized_pnl=-10.0, realized_pnl_percent=-5.0,
                entry_price=0.5, size=100, trading_mode="live",
                strategy_name="Alpha", source="telegram",
                opened_at="2025-01-02T10:00:00Z", closed_at="2025-01-02T12:00:00Z"
            ),
        ]
        for p in positions:
            db_session.add(p)
        await db_session.commit()

        response = await client.get("/api/analytics/summary")
        assert response.status_code == 200
        data = response.json()

        assert data["totals"]["basic"]["total_trades"] == 2
        assert data["totals"]["basic"]["total_realized_pnl"] == 20.0
        assert data["totals"]["basic"]["win_rate"] == 50.0

    @pytest.mark.asyncio
    async def test_summary_with_trading_mode_filter(self, client, db_session):
        """Test summary filtered by trading mode."""
        positions = [
            Position(id=1, status="closed", realized_pnl=30.0, trading_mode="live",
                     entry_price=0.5, size=100),
            Position(id=2, status="closed", realized_pnl=20.0, trading_mode="paper",
                     entry_price=0.5, size=100),
        ]
        for p in positions:
            db_session.add(p)
        await db_session.commit()

        response = await client.get("/api/analytics/summary?trading_mode=live")
        assert response.status_code == 200
        data = response.json()

        assert data["totals"]["basic"]["total_trades"] == 1
        assert data["totals"]["basic"]["total_realized_pnl"] == 30.0

    @pytest.mark.asyncio
    async def test_summary_with_group_by(self, client, db_session):
        """Test summary grouped by strategy."""
        positions = [
            Position(id=1, status="closed", realized_pnl=30.0, strategy_name="Alpha",
                     entry_price=0.5, size=100),
            Position(id=2, status="closed", realized_pnl=20.0, strategy_name="Beta",
                     entry_price=0.5, size=100),
            Position(id=3, status="closed", realized_pnl=10.0, strategy_name="Alpha",
                     entry_price=0.5, size=100),
        ]
        for p in positions:
            db_session.add(p)
        await db_session.commit()

        response = await client.get("/api/analytics/summary?group_by=strategy_name")
        assert response.status_code == 200
        data = response.json()

        assert len(data["groups"]) == 2
        alpha = next(g for g in data["groups"] if g["group_value"] == "Alpha")
        assert alpha["summary"]["basic"]["total_realized_pnl"] == 40.0
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_analytics_routes.py -v`
Expected: FAIL (route not found)

**Step 3: Implement analytics routes**

```python
# backend/app/routes/analytics.py
"""Analytics API routes."""
from typing import Annotated
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from ..models.position import Position
from ..models.analytics import (
    AnalyticsSummaryResponse,
    GroupedAnalytics,
    TimeseriesResponse,
    TimeseriesPoint,
    HeatmapResponse,
    HeatmapCell,
    TradesResponse,
    TradeRecord,
)
from ..services.analytics import AnalyticsCalculator, AnalyticsFilter
from ..auth.security import get_current_user

router = APIRouter(
    prefix="/api/analytics",
    tags=["analytics"],
    dependencies=[Depends(get_current_user)]
)


@router.get("/summary", response_model=AnalyticsSummaryResponse)
async def get_analytics_summary(
    db: Annotated[AsyncSession, Depends(get_db)],
    trading_mode: str | None = None,
    status: str | None = None,
    strategy_name: str | None = None,
    source: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    group_by: str | None = None,
):
    """Get analytics summary with optional filtering and grouping."""
    # Fetch all positions
    result = await db.execute(select(Position))
    all_positions = result.scalars().all()

    # Apply filters
    filters_applied = {
        k: v for k, v in {
            "trading_mode": trading_mode,
            "status": status,
            "strategy_name": strategy_name,
            "source": source,
            "start_date": start_date,
            "end_date": end_date,
        }.items() if v is not None
    }

    filtered = AnalyticsFilter.apply(
        all_positions,
        trading_mode=trading_mode,
        status=status,
        strategy_name=strategy_name,
        source=source,
        start_date=start_date,
        end_date=end_date,
    )

    # Calculate totals
    calc = AnalyticsCalculator(filtered)
    totals = calc.calculate_summary(filters_applied)

    # Calculate groups if requested
    groups = []
    if group_by:
        grouped = AnalyticsFilter.group_by(filtered, group_by)
        for group_value, group_positions in grouped.items():
            group_calc = AnalyticsCalculator(group_positions)
            groups.append(GroupedAnalytics(
                group_key=group_by,
                group_value=group_value,
                summary=group_calc.calculate_summary(),
            ))

    return AnalyticsSummaryResponse(totals=totals, groups=groups)


@router.get("/timeseries", response_model=TimeseriesResponse)
async def get_analytics_timeseries(
    db: Annotated[AsyncSession, Depends(get_db)],
    metric: str = Query(default="equity", enum=["equity", "pnl", "drawdown", "win_rate"]),
    granularity: str = Query(default="daily", enum=["daily", "weekly", "monthly"]),
    trading_mode: str | None = None,
    strategy_name: str | None = None,
    source: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
):
    """Get timeseries data for charts."""
    result = await db.execute(select(Position))
    all_positions = result.scalars().all()

    filtered = AnalyticsFilter.apply(
        all_positions,
        trading_mode=trading_mode,
        strategy_name=strategy_name,
        source=source,
        start_date=start_date,
        end_date=end_date,
    )

    calc = AnalyticsCalculator(filtered)

    if metric == "equity":
        data = calc.calculate_equity_timeseries(granularity)
    elif metric == "drawdown":
        data = calc.calculate_drawdown_timeseries(granularity)
    else:
        data = calc.calculate_equity_timeseries(granularity)

    return TimeseriesResponse(
        metric=metric,
        granularity=granularity,
        data=data,
    )


@router.get("/heatmap", response_model=HeatmapResponse)
async def get_analytics_heatmap(
    db: Annotated[AsyncSession, Depends(get_db)],
    dimension: str = Query(default="day_of_week", enum=["day_of_week", "hour_of_day"]),
    metric: str = Query(default="pnl", enum=["pnl", "win_rate", "trade_count"]),
    trading_mode: str | None = None,
):
    """Get heatmap data for time-based analysis."""
    from datetime import datetime
    from collections import defaultdict

    result = await db.execute(select(Position).where(Position.status == "closed"))
    all_positions = result.scalars().all()

    filtered = AnalyticsFilter.apply(all_positions, trading_mode=trading_mode)

    # Group by dimension
    buckets: dict[str, list] = defaultdict(list)

    for p in filtered:
        if not p.closed_at:
            continue
        try:
            dt = datetime.fromisoformat(p.closed_at.replace("Z", "+00:00"))
            if dimension == "day_of_week":
                key = dt.strftime("%A")
            elif dimension == "hour_of_day":
                key = str(dt.hour)
            else:
                key = "unknown"
            buckets[key].append(p)
        except (ValueError, TypeError):
            pass

    # Calculate metric per bucket
    cells = []
    for key, positions in buckets.items():
        if metric == "pnl":
            value = sum(p.realized_pnl or 0 for p in positions)
        elif metric == "win_rate":
            wins = len([p for p in positions if (p.realized_pnl or 0) > 0])
            value = (wins / len(positions) * 100) if positions else 0
        else:  # trade_count
            value = len(positions)

        cells.append(HeatmapCell(
            x=key,
            value=round(value, 2),
            count=len(positions),
        ))

    return HeatmapResponse(
        dimension=dimension,
        metric=metric,
        cells=cells,
    )


@router.get("/trades", response_model=TradesResponse)
async def get_analytics_trades(
    db: Annotated[AsyncSession, Depends(get_db)],
    sort_by: str = "closed_at",
    order: str = "desc",
    limit: int = 100,
    offset: int = 0,
    trading_mode: str | None = None,
    status: str | None = None,
    strategy_name: str | None = None,
    source: str | None = None,
):
    """Get paginated trades list."""
    from datetime import datetime

    result = await db.execute(select(Position))
    all_positions = result.scalars().all()

    filtered = AnalyticsFilter.apply(
        all_positions,
        trading_mode=trading_mode,
        status=status,
        strategy_name=strategy_name,
        source=source,
    )

    # Sort
    def sort_key(p):
        val = getattr(p, sort_by, None)
        if val is None:
            return "" if order == "desc" else "zzz"
        return val

    sorted_positions = sorted(filtered, key=sort_key, reverse=(order == "desc"))

    # Paginate
    total_count = len(sorted_positions)
    paginated = sorted_positions[offset:offset + limit]

    # Convert to TradeRecord
    trades = []
    for p in paginated:
        hold_time = None
        if p.opened_at and p.closed_at:
            try:
                opened = datetime.fromisoformat(p.opened_at.replace("Z", "+00:00"))
                closed = datetime.fromisoformat(p.closed_at.replace("Z", "+00:00"))
                hold_time = round((closed - opened).total_seconds() / 3600, 2)
            except (ValueError, TypeError):
                pass

        trades.append(TradeRecord(
            id=p.id,
            market_question=p.market_question,
            side=p.side,
            entry_price=p.entry_price,
            exit_price=p.exit_price,
            size=p.size,
            realized_pnl=p.realized_pnl,
            realized_pnl_percent=p.realized_pnl_percent,
            status=p.status,
            strategy_name=p.strategy_name,
            source=p.source,
            trading_mode=p.trading_mode,
            opened_at=p.opened_at,
            closed_at=p.closed_at,
            hold_time_hours=hold_time,
        ))

    return TradesResponse(
        trades=trades,
        total_count=total_count,
        limit=limit,
        offset=offset,
    )


@router.get("/filters")
async def get_filter_options(
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get available filter options."""
    result = await db.execute(select(Position))
    all_positions = result.scalars().all()

    return AnalyticsFilter.get_filter_options(all_positions)
```

**Step 4: Register router**

Modify `backend/app/routes/__init__.py` to include:

```python
from .analytics import router as analytics_router
```

And add to the router list.

**Step 5: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_analytics_routes.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add backend/app/routes/analytics.py backend/app/routes/__init__.py backend/tests/test_analytics_routes.py
git commit -m "feat(analytics): add REST API endpoints"
```

---

## Task 8: Backend WebSocket Analytics Events

**Files:**
- Modify: `backend/app/services/trading/executor.py` (or wherever position changes happen)
- Modify: existing WebSocket handler

**Step 1: Add analytics_update event type**

Find the existing WebSocket broadcast logic and add a new event type `analytics_update` that gets triggered when positions change.

**Step 2: Broadcast analytics on position change**

After any position is created, updated, or closed, broadcast:

```python
await websocket_manager.broadcast({
    "type": "analytics_update",
    "payload": {
        "trigger": "position_changed",
        "position_id": position.id,
    },
    "timestamp": datetime.now(UTC).isoformat(),
})
```

**Step 3: Commit**

```bash
git add backend/app/services/
git commit -m "feat(analytics): broadcast WebSocket events on position changes"
```

---

## Task 9: Frontend TypeScript Types

**Files:**
- Create: `frontend/src/types/analytics.ts`

**Step 1: Create TypeScript types**

```typescript
// frontend/src/types/analytics.ts

export interface BasicMetrics {
  total_realized_pnl: number;
  total_realized_pnl_percent: number;
  total_unrealized_pnl: number;
  total_unrealized_pnl_percent: number;
  total_trades: number;
  open_trades: number;
  closed_trades: number;
  wins: number;
  losses: number;
  win_rate: number;
  avg_win: number;
  avg_loss: number;
  best_trade: number;
  worst_trade: number;
}

export interface RiskMetrics {
  sharpe_ratio: number | null;
  sortino_ratio: number | null;
  max_drawdown: number;
  max_drawdown_percent: number;
  current_drawdown: number;
  current_drawdown_percent: number;
  risk_reward_ratio: number | null;
  calmar_ratio: number | null;
}

export interface EfficiencyMetrics {
  profit_factor: number | null;
  expectancy: number;
  avg_hold_time_hours: number | null;
  trades_per_day: number;
  longest_win_streak: number;
  longest_loss_streak: number;
  current_streak: number;
  current_streak_type: "win" | "loss" | "none";
}

export interface AnalyticsSummary {
  basic: BasicMetrics;
  risk: RiskMetrics;
  efficiency: EfficiencyMetrics;
  total_invested: number;
  filters_applied: Record<string, string>;
}

export interface GroupedAnalytics {
  group_key: string;
  group_value: string;
  summary: AnalyticsSummary;
}

export interface AnalyticsSummaryResponse {
  totals: AnalyticsSummary;
  groups: GroupedAnalytics[];
}

export interface TimeseriesPoint {
  timestamp: string;
  value: number;
  group: string | null;
}

export interface TimeseriesResponse {
  metric: string;
  granularity: string;
  data: TimeseriesPoint[];
}

export interface HeatmapCell {
  x: string;
  y: string | null;
  value: number;
  count: number;
}

export interface HeatmapResponse {
  dimension: string;
  metric: string;
  cells: HeatmapCell[];
}

export interface TradeRecord {
  id: number;
  market_question: string | null;
  side: string | null;
  entry_price: number | null;
  exit_price: number | null;
  size: number | null;
  realized_pnl: number | null;
  realized_pnl_percent: number | null;
  status: string;
  strategy_name: string | null;
  source: string | null;
  trading_mode: string | null;
  opened_at: string | null;
  closed_at: string | null;
  hold_time_hours: number | null;
}

export interface TradesResponse {
  trades: TradeRecord[];
  total_count: number;
  limit: number;
  offset: number;
}

export interface AnalyticsFilters {
  trading_mode?: "live" | "paper" | "all";
  status?: "open" | "closed" | "all";
  strategy_name?: string;
  source?: string;
  start_date?: string;
  end_date?: string;
  group_by?: string;
}

export interface FilterOptions {
  strategies: string[];
  sources: string[];
  trading_modes: string[];
}
```

**Step 2: Commit**

```bash
git add frontend/src/types/analytics.ts
git commit -m "feat(analytics): add frontend TypeScript types"
```

---

## Task 10: Frontend API Client

**Files:**
- Create: `frontend/src/lib/analytics-api.ts`

**Step 1: Create API client**

```typescript
// frontend/src/lib/analytics-api.ts

import type {
  AnalyticsSummaryResponse,
  TimeseriesResponse,
  HeatmapResponse,
  TradesResponse,
  AnalyticsFilters,
  FilterOptions,
} from "@/types/analytics";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function getAuthHeaders(): HeadersInit {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

function buildQueryString(params: Record<string, string | undefined>): string {
  const filtered = Object.entries(params)
    .filter(([, v]) => v !== undefined && v !== "all")
    .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v!)}`);
  return filtered.length > 0 ? `?${filtered.join("&")}` : "";
}

export const analyticsApi = {
  async getSummary(filters: AnalyticsFilters = {}): Promise<AnalyticsSummaryResponse> {
    const query = buildQueryString({
      trading_mode: filters.trading_mode,
      status: filters.status,
      strategy_name: filters.strategy_name,
      source: filters.source,
      start_date: filters.start_date,
      end_date: filters.end_date,
      group_by: filters.group_by,
    });

    const response = await fetch(`${API_URL}/api/analytics/summary${query}`, {
      headers: getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch analytics summary: ${response.status}`);
    }

    return response.json();
  },

  async getTimeseries(
    metric: "equity" | "pnl" | "drawdown" | "win_rate" = "equity",
    granularity: "daily" | "weekly" | "monthly" = "daily",
    filters: AnalyticsFilters = {}
  ): Promise<TimeseriesResponse> {
    const query = buildQueryString({
      metric,
      granularity,
      trading_mode: filters.trading_mode,
      strategy_name: filters.strategy_name,
      source: filters.source,
      start_date: filters.start_date,
      end_date: filters.end_date,
    });

    const response = await fetch(`${API_URL}/api/analytics/timeseries${query}`, {
      headers: getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch timeseries: ${response.status}`);
    }

    return response.json();
  },

  async getHeatmap(
    dimension: "day_of_week" | "hour_of_day" = "day_of_week",
    metric: "pnl" | "win_rate" | "trade_count" = "pnl",
    tradingMode?: string
  ): Promise<HeatmapResponse> {
    const query = buildQueryString({
      dimension,
      metric,
      trading_mode: tradingMode,
    });

    const response = await fetch(`${API_URL}/api/analytics/heatmap${query}`, {
      headers: getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch heatmap: ${response.status}`);
    }

    return response.json();
  },

  async getTrades(
    filters: AnalyticsFilters = {},
    sortBy = "closed_at",
    order = "desc",
    limit = 100,
    offset = 0
  ): Promise<TradesResponse> {
    const query = buildQueryString({
      trading_mode: filters.trading_mode,
      status: filters.status,
      strategy_name: filters.strategy_name,
      source: filters.source,
      sort_by: sortBy,
      order,
      limit: String(limit),
      offset: String(offset),
    });

    const response = await fetch(`${API_URL}/api/analytics/trades${query}`, {
      headers: getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch trades: ${response.status}`);
    }

    return response.json();
  },

  async getFilterOptions(): Promise<FilterOptions> {
    const response = await fetch(`${API_URL}/api/analytics/filters`, {
      headers: getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch filter options: ${response.status}`);
    }

    return response.json();
  },
};
```

**Step 2: Commit**

```bash
git add frontend/src/lib/analytics-api.ts
git commit -m "feat(analytics): add frontend API client"
```

---

## Task 11: Frontend useAnalytics Hook

**Files:**
- Create: `frontend/src/hooks/use-analytics.ts`

**Step 1: Create the hook**

```typescript
// frontend/src/hooks/use-analytics.ts
"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { analyticsApi } from "@/lib/analytics-api";
import { useWebSocket } from "./use-websocket";
import type {
  AnalyticsSummaryResponse,
  TimeseriesResponse,
  HeatmapResponse,
  TradesResponse,
  AnalyticsFilters,
  FilterOptions,
} from "@/types/analytics";

export interface UseAnalyticsOptions {
  initialFilters?: AnalyticsFilters;
  autoRefresh?: boolean;
  refreshInterval?: number;
}

export interface UseAnalyticsReturn {
  // Data
  summary: AnalyticsSummaryResponse | null;
  equityTimeseries: TimeseriesResponse | null;
  drawdownTimeseries: TimeseriesResponse | null;
  heatmap: HeatmapResponse | null;
  trades: TradesResponse | null;
  filterOptions: FilterOptions | null;

  // State
  isLoading: boolean;
  error: string | null;
  isConnected: boolean;

  // Actions
  filters: AnalyticsFilters;
  setFilters: (filters: AnalyticsFilters) => void;
  refresh: () => Promise<void>;
  loadMoreTrades: () => Promise<void>;
}

export function useAnalytics(options: UseAnalyticsOptions = {}): UseAnalyticsReturn {
  const { initialFilters = { trading_mode: "live" }, autoRefresh = true } = options;

  const [filters, setFiltersState] = useState<AnalyticsFilters>(initialFilters);
  const [summary, setSummary] = useState<AnalyticsSummaryResponse | null>(null);
  const [equityTimeseries, setEquityTimeseries] = useState<TimeseriesResponse | null>(null);
  const [drawdownTimeseries, setDrawdownTimeseries] = useState<TimeseriesResponse | null>(null);
  const [heatmap, setHeatmap] = useState<HeatmapResponse | null>(null);
  const [trades, setTrades] = useState<TradesResponse | null>(null);
  const [filterOptions, setFilterOptions] = useState<FilterOptions | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const tradesOffset = useRef(0);

  const fetchAllData = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const [summaryData, equityData, drawdownData, heatmapData, tradesData, options] =
        await Promise.all([
          analyticsApi.getSummary({ ...filters, group_by: "strategy_name" }),
          analyticsApi.getTimeseries("equity", "daily", filters),
          analyticsApi.getTimeseries("drawdown", "daily", filters),
          analyticsApi.getHeatmap("day_of_week", "pnl", filters.trading_mode),
          analyticsApi.getTrades(filters, "closed_at", "desc", 100, 0),
          analyticsApi.getFilterOptions(),
        ]);

      setSummary(summaryData);
      setEquityTimeseries(equityData);
      setDrawdownTimeseries(drawdownData);
      setHeatmap(heatmapData);
      setTrades(tradesData);
      setFilterOptions(options);
      tradesOffset.current = 100;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch analytics");
    } finally {
      setIsLoading(false);
    }
  }, [filters]);

  const loadMoreTrades = useCallback(async () => {
    if (!trades) return;

    try {
      const moreTrades = await analyticsApi.getTrades(
        filters,
        "closed_at",
        "desc",
        100,
        tradesOffset.current
      );

      setTrades(prev => prev ? {
        ...prev,
        trades: [...prev.trades, ...moreTrades.trades],
      } : moreTrades);

      tradesOffset.current += 100;
    } catch (err) {
      console.error("Failed to load more trades:", err);
    }
  }, [filters, trades]);

  const setFilters = useCallback((newFilters: AnalyticsFilters) => {
    setFiltersState(newFilters);
    tradesOffset.current = 0;
  }, []);

  // WebSocket for real-time updates
  const { isConnected } = useWebSocket({
    enabled: autoRefresh,
    onPositionClosed: () => fetchAllData(),
    onPositionOpened: () => fetchAllData(),
    onPositionUpdate: () => {
      // Debounced refresh for position updates
      // Only refresh summary for minor updates
      analyticsApi.getSummary({ ...filters, group_by: "strategy_name" })
        .then(setSummary)
        .catch(console.error);
    },
  });

  // Initial fetch
  useEffect(() => {
    fetchAllData();
  }, [fetchAllData]);

  return {
    summary,
    equityTimeseries,
    drawdownTimeseries,
    heatmap,
    trades,
    filterOptions,
    isLoading,
    error,
    isConnected,
    filters,
    setFilters,
    refresh: fetchAllData,
    loadMoreTrades,
  };
}
```

**Step 2: Commit**

```bash
git add frontend/src/hooks/use-analytics.ts
git commit -m "feat(analytics): add useAnalytics hook with WebSocket support"
```

---

## Task 12: Install Lightweight Charts

**Step 1: Install the package**

Run: `cd frontend && npm install lightweight-charts`

**Step 2: Commit**

```bash
git add frontend/package.json frontend/package-lock.json
git commit -m "chore: add lightweight-charts dependency"
```

---

## Task 13: Frontend KPI Cards Component

**Files:**
- Create: `frontend/src/components/analytics/KpiCards.tsx`

**Step 1: Create the component**

```typescript
// frontend/src/components/analytics/KpiCards.tsx
"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import {
  TrendingUp,
  TrendingDown,
  Target,
  Activity,
  DollarSign,
  AlertTriangle,
} from "lucide-react";
import type { AnalyticsSummary } from "@/types/analytics";

interface KpiCardsProps {
  summary: AnalyticsSummary;
  isLoading?: boolean;
}

function formatCurrency(value: number): string {
  const prefix = value >= 0 ? "+" : "";
  return `${prefix}$${Math.abs(value).toLocaleString(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

function formatPercent(value: number): string {
  const prefix = value >= 0 ? "+" : "";
  return `${prefix}${value.toFixed(2)}%`;
}

function formatMetric(value: number | null, fallback = "N/A"): string {
  if (value === null) return fallback;
  return value.toFixed(2);
}

export function KpiCards({ summary, isLoading }: KpiCardsProps) {
  const { basic, risk, efficiency } = summary;

  const cards = [
    {
      title: "Total P&L",
      icon: DollarSign,
      value: formatCurrency(basic.total_realized_pnl),
      valueClass: basic.total_realized_pnl >= 0 ? "text-green-500" : "text-red-500",
      subtitle: `Unrealized: ${formatCurrency(basic.total_unrealized_pnl)}`,
    },
    {
      title: "Win Rate",
      icon: Target,
      value: `${basic.win_rate.toFixed(1)}%`,
      valueClass: basic.win_rate >= 50 ? "text-green-500" : "text-yellow-500",
      subtitle: `${basic.wins}W / ${basic.losses}L`,
      progress: basic.win_rate,
    },
    {
      title: "Sharpe Ratio",
      icon: risk.sharpe_ratio && risk.sharpe_ratio > 1 ? TrendingUp : TrendingDown,
      value: formatMetric(risk.sharpe_ratio),
      valueClass: (risk.sharpe_ratio ?? 0) > 1 ? "text-green-500" : "text-yellow-500",
      subtitle: `Sortino: ${formatMetric(risk.sortino_ratio)}`,
    },
    {
      title: "Max Drawdown",
      icon: AlertTriangle,
      value: formatCurrency(-risk.max_drawdown),
      valueClass: "text-red-500",
      subtitle: formatPercent(-risk.max_drawdown_percent),
    },
    {
      title: "Profit Factor",
      icon: Activity,
      value: formatMetric(efficiency.profit_factor),
      valueClass: (efficiency.profit_factor ?? 0) > 1.5 ? "text-green-500" : "text-yellow-500",
      subtitle: `Avg Win: $${basic.avg_win.toFixed(2)} | Avg Loss: $${basic.avg_loss.toFixed(2)}`,
    },
    {
      title: "Open Positions",
      icon: Activity,
      value: String(basic.open_trades),
      valueClass: "text-foreground",
      subtitle: `${basic.total_trades} total closed`,
    },
  ];

  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
        {Array.from({ length: 6 }).map((_, i) => (
          <Card key={i}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <div className="h-4 w-24 bg-muted animate-pulse rounded" />
            </CardHeader>
            <CardContent>
              <div className="h-8 w-20 bg-muted animate-pulse rounded mb-2" />
              <div className="h-3 w-32 bg-muted animate-pulse rounded" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
      {cards.map((card) => (
        <Card key={card.title}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{card.title}</CardTitle>
            <card.icon className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${card.valueClass}`}>
              {card.value}
            </div>
            {card.progress !== undefined && (
              <Progress value={card.progress} className="mt-2" />
            )}
            <p className="text-xs text-muted-foreground mt-1">{card.subtitle}</p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
```

**Step 2: Commit**

```bash
git add frontend/src/components/analytics/KpiCards.tsx
git commit -m "feat(analytics): add KPI cards component"
```

---

## Task 14: Frontend Equity Curve Component (Lightweight Charts)

**Files:**
- Create: `frontend/src/components/analytics/EquityCurve.tsx`

**Step 1: Create the component**

```typescript
// frontend/src/components/analytics/EquityCurve.tsx
"use client";

import { useEffect, useRef } from "react";
import { createChart, ColorType, IChartApi, ISeriesApi, LineData } from "lightweight-charts";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import type { TimeseriesResponse } from "@/types/analytics";

interface EquityCurveProps {
  data: TimeseriesResponse | null;
  isLoading?: boolean;
  onGranularityChange?: (granularity: "daily" | "weekly" | "monthly") => void;
  granularity?: "daily" | "weekly" | "monthly";
}

export function EquityCurve({
  data,
  isLoading,
  onGranularityChange,
  granularity = "daily",
}: EquityCurveProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<"Area"> | null>(null);

  useEffect(() => {
    if (!chartContainerRef.current) return;

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: "hsl(var(--foreground))",
      },
      grid: {
        vertLines: { color: "hsl(var(--border))" },
        horzLines: { color: "hsl(var(--border))" },
      },
      width: chartContainerRef.current.clientWidth,
      height: 300,
      rightPriceScale: {
        borderVisible: false,
      },
      timeScale: {
        borderVisible: false,
      },
    });

    const areaSeries = chart.addAreaSeries({
      lineColor: "hsl(var(--chart-1))",
      topColor: "hsla(var(--chart-1), 0.4)",
      bottomColor: "hsla(var(--chart-1), 0.1)",
      lineWidth: 2,
    });

    chartRef.current = chart;
    seriesRef.current = areaSeries;

    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({ width: chartContainerRef.current.clientWidth });
      }
    };

    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      chart.remove();
    };
  }, []);

  useEffect(() => {
    if (!seriesRef.current || !data?.data) return;

    const chartData: LineData[] = data.data.map((point) => ({
      time: point.timestamp as string,
      value: point.value,
    }));

    seriesRef.current.setData(chartData);
    chartRef.current?.timeScale().fitContent();
  }, [data]);

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle>Equity Curve</CardTitle>
          <CardDescription>Cumulative P&L over time</CardDescription>
        </div>
        <ToggleGroup
          type="single"
          value={granularity}
          onValueChange={(v) => v && onGranularityChange?.(v as "daily" | "weekly" | "monthly")}
        >
          <ToggleGroupItem value="daily" size="sm">1D</ToggleGroupItem>
          <ToggleGroupItem value="weekly" size="sm">1W</ToggleGroupItem>
          <ToggleGroupItem value="monthly" size="sm">1M</ToggleGroupItem>
        </ToggleGroup>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="h-[300px] bg-muted animate-pulse rounded" />
        ) : (
          <div ref={chartContainerRef} className="h-[300px]" />
        )}
      </CardContent>
    </Card>
  );
}
```

**Step 2: Commit**

```bash
git add frontend/src/components/analytics/EquityCurve.tsx
git commit -m "feat(analytics): add equity curve component with Lightweight Charts"
```

---

## Task 15: Frontend Remaining Components

**Files:**
- Create: `frontend/src/components/analytics/ModeToggle.tsx`
- Create: `frontend/src/components/analytics/FilterBar.tsx`
- Create: `frontend/src/components/analytics/DrawdownChart.tsx`
- Create: `frontend/src/components/analytics/PerformanceHeatmap.tsx`
- Create: `frontend/src/components/analytics/StrategyTable.tsx`
- Create: `frontend/src/components/analytics/TradesTable.tsx`
- Create: `frontend/src/components/analytics/index.ts`

These follow the same pattern - create each component using ShadCN primitives and Lightweight Charts where appropriate. See the design document for layouts.

**Step by step:** Create each component, test it renders, commit.

---

## Task 16: Frontend Analytics Page

**Files:**
- Replace: `frontend/src/app/statistics/page.tsx`

**Step 1: Replace the page with new implementation**

```typescript
// frontend/src/app/statistics/page.tsx
"use client";

import { useAnalytics } from "@/hooks/use-analytics";
import {
  KpiCards,
  ModeToggle,
  FilterBar,
  EquityCurve,
  DrawdownChart,
  PerformanceHeatmap,
  StrategyTable,
  TradesTable,
} from "@/components/analytics";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Wifi, WifiOff } from "lucide-react";

export default function AnalyticsPage() {
  const {
    summary,
    equityTimeseries,
    drawdownTimeseries,
    heatmap,
    trades,
    filterOptions,
    isLoading,
    error,
    isConnected,
    filters,
    setFilters,
    refresh,
    loadMoreTrades,
  } = useAnalytics({ initialFilters: { trading_mode: "live" } });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Analytics</h1>
          <p className="text-muted-foreground">
            Trading performance metrics and analysis
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant={isConnected ? "default" : "secondary"}>
            {isConnected ? (
              <><Wifi className="h-3 w-3 mr-1" /> Live</>
            ) : (
              <><WifiOff className="h-3 w-3 mr-1" /> Offline</>
            )}
          </Badge>
        </div>
      </div>

      {/* Error */}
      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Mode Toggle */}
      <ModeToggle
        value={filters.trading_mode || "live"}
        onChange={(mode) => setFilters({ ...filters, trading_mode: mode })}
      />

      {/* Filter Bar */}
      <FilterBar
        filters={filters}
        options={filterOptions}
        onChange={setFilters}
        onRefresh={refresh}
      />

      {/* KPI Cards */}
      {summary && <KpiCards summary={summary.totals} isLoading={isLoading} />}

      {/* Charts Row */}
      <div className="grid gap-4 lg:grid-cols-2">
        <EquityCurve data={equityTimeseries} isLoading={isLoading} />
        <DrawdownChart data={drawdownTimeseries} isLoading={isLoading} />
      </div>

      {/* Heatmap */}
      <PerformanceHeatmap data={heatmap} isLoading={isLoading} />

      {/* Strategy Comparison */}
      {summary && summary.groups.length > 0 && (
        <StrategyTable groups={summary.groups} isLoading={isLoading} />
      )}

      {/* Trades Table */}
      <TradesTable
        data={trades}
        isLoading={isLoading}
        onLoadMore={loadMoreTrades}
      />
    </div>
  );
}
```

**Step 2: Commit**

```bash
git add frontend/src/app/statistics/page.tsx
git commit -m "feat(analytics): implement complete analytics dashboard page"
```

---

## Task 17: Integration Testing

**Step 1: Start backend and frontend**

```bash
cd backend && uvicorn main:app --reload &
cd frontend && npm run dev &
```

**Step 2: Verify all endpoints work**

```bash
curl http://localhost:8000/api/analytics/summary
curl http://localhost:8000/api/analytics/timeseries
curl http://localhost:8000/api/analytics/heatmap
curl http://localhost:8000/api/analytics/trades
```

**Step 3: Open browser and test UI**

- Navigate to http://localhost:3000/statistics
- Verify KPI cards display
- Verify charts render
- Verify mode toggle works
- Verify filters apply correctly
- Verify WebSocket connection indicator

**Step 4: Final commit**

```bash
git add .
git commit -m "feat(analytics): complete statistics & analytics implementation"
```

---

## Summary

This plan implements the Statistics & Analytics feature in 17 tasks:

1. **Tasks 1-6**: Backend analytics service (models, calculator, filters)
2. **Task 7**: Backend REST API endpoints
3. **Task 8**: Backend WebSocket integration
4. **Tasks 9-11**: Frontend types, API client, hook
5. **Tasks 12-15**: Frontend components (Lightweight Charts + ShadCN)
6. **Task 16**: Frontend page assembly
7. **Task 17**: Integration testing

Each task is TDD-driven with specific tests, implementations, and commits.
