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
