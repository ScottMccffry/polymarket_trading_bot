"""Analytics API routes."""
from datetime import datetime
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
    result = await db.execute(select(Position))
    all_positions = result.scalars().all()

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

    calc = AnalyticsCalculator(filtered)
    totals = calc.calculate_summary(filters_applied)

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
    metric: str = Query(default="equity", pattern="^(equity|pnl|drawdown)$"),
    granularity: str = Query(default="daily", pattern="^(daily|weekly|monthly)$"),
    trading_mode: str | None = None,
    status: str | None = None,
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
        status=status,
        strategy_name=strategy_name,
        source=source,
        start_date=start_date,
        end_date=end_date,
    )

    calc = AnalyticsCalculator(filtered)

    if metric == "equity":
        data = calc.calculate_equity_timeseries(granularity=granularity)
    elif metric == "drawdown":
        data = calc.calculate_drawdown_timeseries(granularity=granularity)
    else:  # pnl - same as equity for now
        data = calc.calculate_equity_timeseries(granularity=granularity)

    return TimeseriesResponse(metric=metric, granularity=granularity, data=data)


@router.get("/trades", response_model=TradesResponse)
async def get_analytics_trades(
    db: Annotated[AsyncSession, Depends(get_db)],
    sort_by: str = Query(default="closed_at", pattern="^(realized_pnl|opened_at|closed_at|size)$"),
    order: str = Query(default="desc", pattern="^(asc|desc)$"),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    trading_mode: str | None = None,
    status: str | None = None,
    strategy_name: str | None = None,
    source: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
):
    """Get paginated trades list."""
    result = await db.execute(select(Position))
    all_positions = result.scalars().all()

    filtered = AnalyticsFilter.apply(
        all_positions,
        trading_mode=trading_mode,
        status=status,
        strategy_name=strategy_name,
        source=source,
        start_date=start_date,
        end_date=end_date,
    )

    # Sort positions
    def get_sort_key(p: Position):
        if sort_by == "realized_pnl":
            return p.realized_pnl or 0
        elif sort_by == "opened_at":
            return p.opened_at or ""
        elif sort_by == "closed_at":
            return p.closed_at or ""
        elif sort_by == "size":
            return p.size or 0
        return p.closed_at or ""

    sorted_positions = sorted(filtered, key=get_sort_key, reverse=(order == "desc"))
    total_count = len(sorted_positions)
    paginated = sorted_positions[offset:offset + limit]

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
            status=p.status or "unknown",
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


@router.get("/heatmap", response_model=HeatmapResponse)
async def get_analytics_heatmap(
    db: Annotated[AsyncSession, Depends(get_db)],
    dimension: str = Query(default="day_of_week", pattern="^(day_of_week|hour_of_day|month)$"),
    metric: str = Query(default="pnl", pattern="^(pnl|win_rate|trade_count)$"),
    trading_mode: str | None = None,
    status: str | None = None,
    strategy_name: str | None = None,
    source: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
):
    """Get heatmap data for pattern analysis."""
    result = await db.execute(select(Position))
    all_positions = result.scalars().all()

    filtered = AnalyticsFilter.apply(
        all_positions,
        trading_mode=trading_mode,
        status=status,
        strategy_name=strategy_name,
        source=source,
        start_date=start_date,
        end_date=end_date,
    )

    # Only use closed positions for heatmap analysis
    closed = [p for p in filtered if p.status == "closed" and p.closed_at]

    # Group by dimension
    buckets: dict[str, list[Position]] = {}
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    for p in closed:
        try:
            dt = datetime.fromisoformat(p.closed_at.replace("Z", "+00:00"))
            if dimension == "day_of_week":
                key = day_names[dt.weekday()]
            elif dimension == "hour_of_day":
                key = str(dt.hour)
            elif dimension == "month":
                key = month_names[dt.month - 1]
            else:
                key = "Unknown"

            if key not in buckets:
                buckets[key] = []
            buckets[key].append(p)
        except (ValueError, TypeError):
            pass

    # Calculate metric for each bucket
    cells = []
    for key, positions in buckets.items():
        count = len(positions)
        if metric == "pnl":
            value = sum(p.realized_pnl or 0 for p in positions)
        elif metric == "win_rate":
            wins = len([p for p in positions if (p.realized_pnl or 0) > 0])
            value = (wins / count * 100) if count > 0 else 0
        elif metric == "trade_count":
            value = float(count)
        else:
            value = 0

        cells.append(HeatmapCell(x=key, value=round(value, 2), count=count))

    # Sort cells by dimension order
    if dimension == "day_of_week":
        cells.sort(key=lambda c: day_names.index(c.x) if c.x in day_names else 99)
    elif dimension == "hour_of_day":
        cells.sort(key=lambda c: int(c.x) if c.x.isdigit() else 99)
    elif dimension == "month":
        cells.sort(key=lambda c: month_names.index(c.x) if c.x in month_names else 99)

    return HeatmapResponse(dimension=dimension, metric=metric, cells=cells)


@router.get("/filter-options")
async def get_filter_options(
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get available filter options from positions data."""
    result = await db.execute(select(Position))
    all_positions = result.scalars().all()

    options = AnalyticsFilter.get_filter_options(all_positions)
    return options
