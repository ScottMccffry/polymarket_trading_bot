"""Dashboard UI routes."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, func
from pathlib import Path

from ...db.session import get_session
from ...models.position import Position, PositionStatus
from ...models.signal import Signal
from ...models.simulation import SimulationState

router = APIRouter()

# Templates
templates_path = Path(__file__).parent.parent.parent.parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_path))


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page."""
    async with get_session() as session:
        # Get simulation state
        stmt = select(SimulationState).where(SimulationState.id == 1)
        result = await session.execute(stmt)
        state = result.scalar_one_or_none()

        # Get open positions
        stmt = (
            select(Position)
            .where(Position.status == PositionStatus.OPEN)
            .order_by(Position.created_at.desc())
        )
        result = await session.execute(stmt)
        positions = list(result.scalars().all())

        # Get recent signals
        stmt = select(Signal).order_by(Signal.created_at.desc()).limit(10)
        result = await session.execute(stmt)
        signals = list(result.scalars().all())

        # Strategy stats
        stmt = (
            select(
                Position.strategy,
                func.count(Position.id).label("count"),
                func.sum(Position.pnl).label("total_pnl"),
            )
            .where(Position.status == PositionStatus.CLOSED)
            .group_by(Position.strategy)
        )
        result = await session.execute(stmt)
        strategy_stats = list(result.all())

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "state": state,
            "positions": positions,
            "signals": signals,
            "strategy_stats": strategy_stats,
        },
    )


@router.get("/positions", response_class=HTMLResponse)
async def positions_page(request: Request):
    """Positions page."""
    async with get_session() as session:
        # Open positions
        stmt = (
            select(Position)
            .where(Position.status == PositionStatus.OPEN)
            .order_by(Position.created_at.desc())
        )
        result = await session.execute(stmt)
        open_positions = list(result.scalars().all())

        # Closed positions
        stmt = (
            select(Position)
            .where(Position.status == PositionStatus.CLOSED)
            .order_by(Position.closed_at.desc())
            .limit(50)
        )
        result = await session.execute(stmt)
        closed_positions = list(result.scalars().all())

    return templates.TemplateResponse(
        "positions.html",
        {
            "request": request,
            "open_positions": open_positions,
            "closed_positions": closed_positions,
        },
    )


@router.get("/strategies", response_class=HTMLResponse)
async def strategies_page(request: Request):
    """Strategies page."""
    from ...trading.strategies.registry import StrategyRegistry

    registry = StrategyRegistry()
    strategies = registry.list_strategies()

    return templates.TemplateResponse(
        "strategies.html",
        {
            "request": request,
            "strategies": strategies,
        },
    )
