from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from ..database import get_db
from ..models.position import Position, PositionResponse, StrategyOverview
from ..auth.security import get_current_user

router = APIRouter(
    prefix="/api/positions",
    tags=["positions"],
    dependencies=[Depends(get_current_user)]
)


@router.get("", response_model=list[PositionResponse])
async def get_positions(
    db: Annotated[AsyncSession, Depends(get_db)],
    status: str | None = None,
    strategy_id: int | None = None,
    limit: int = 100,
    offset: int = 0,
):
    """Get all positions with optional filtering."""
    query = select(Position)

    if status:
        query = query.where(Position.status == status)
    if strategy_id:
        query = query.where(Position.strategy_id == strategy_id)

    query = query.order_by(Position.opened_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    positions = result.scalars().all()
    return positions


@router.get("/open", response_model=list[PositionResponse])
async def get_open_positions(
    db: Annotated[AsyncSession, Depends(get_db)],
    strategy_id: int | None = None,
):
    """Get all open positions."""
    query = select(Position).where(Position.status == "open")

    if strategy_id:
        query = query.where(Position.strategy_id == strategy_id)

    query = query.order_by(Position.opened_at.desc())
    result = await db.execute(query)
    positions = result.scalars().all()
    return positions


@router.get("/closed", response_model=list[PositionResponse])
async def get_closed_positions(
    db: Annotated[AsyncSession, Depends(get_db)],
    strategy_id: int | None = None,
    limit: int = 50,
):
    """Get all closed positions."""
    query = select(Position).where(Position.status == "closed")

    if strategy_id:
        query = query.where(Position.strategy_id == strategy_id)

    query = query.order_by(Position.closed_at.desc()).limit(limit)
    result = await db.execute(query)
    positions = result.scalars().all()
    return positions


@router.get("/strategy/{strategy_id}", response_model=dict)
async def get_positions_by_strategy(
    strategy_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get all positions for a specific strategy with overview."""
    # Get open positions
    open_result = await db.execute(
        select(Position)
        .where(Position.strategy_id == strategy_id, Position.status == "open")
        .order_by(Position.opened_at.desc())
    )
    open_positions = open_result.scalars().all()

    # Get closed positions
    closed_result = await db.execute(
        select(Position)
        .where(Position.strategy_id == strategy_id, Position.status == "closed")
        .order_by(Position.closed_at.desc())
    )
    closed_positions = closed_result.scalars().all()

    # Calculate overview
    total_realized_pnl = sum(p.realized_pnl or 0 for p in closed_positions)
    total_unrealized_pnl = sum(p.unrealized_pnl or 0 for p in open_positions)

    total_invested_closed = sum((p.entry_price or 0) * (p.size or 0) for p in closed_positions)
    total_invested_open = sum((p.entry_price or 0) * (p.size or 0) for p in open_positions)

    total_realized_pnl_percent = (
        (total_realized_pnl / total_invested_closed * 100) if total_invested_closed > 0 else 0
    )
    total_unrealized_pnl_percent = (
        (total_unrealized_pnl / total_invested_open * 100) if total_invested_open > 0 else 0
    )

    winning_trades = len([p for p in closed_positions if (p.realized_pnl or 0) > 0])
    win_rate = (winning_trades / len(closed_positions) * 100) if closed_positions else 0

    # Get strategy name from first position or use default
    strategy_name = "Unknown Strategy"
    if open_positions:
        strategy_name = open_positions[0].strategy_name or strategy_name
    elif closed_positions:
        strategy_name = closed_positions[0].strategy_name or strategy_name

    return {
        "overview": {
            "strategy_id": strategy_id,
            "strategy_name": strategy_name,
            "total_positions": len(open_positions) + len(closed_positions),
            "open_positions_count": len(open_positions),
            "closed_positions_count": len(closed_positions),
            "total_realized_pnl": round(total_realized_pnl, 2),
            "total_realized_pnl_percent": round(total_realized_pnl_percent, 2),
            "total_unrealized_pnl": round(total_unrealized_pnl, 2),
            "total_unrealized_pnl_percent": round(total_unrealized_pnl_percent, 2),
            "win_rate": round(win_rate, 2),
            "total_invested": round(total_invested_closed + total_invested_open, 2),
        },
        "open_positions": open_positions,
        "closed_positions": closed_positions,
    }


@router.get("/overview", response_model=list[dict])
async def get_all_strategies_overview(
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get overview for all strategies with positions."""
    # Get distinct strategy IDs
    result = await db.execute(
        select(Position.strategy_id, Position.strategy_name)
        .distinct()
        .where(Position.strategy_id.isnot(None))
    )
    strategies = result.all()

    overviews = []
    for strategy_id, strategy_name in strategies:
        # Get positions for this strategy
        positions_result = await db.execute(
            select(Position).where(Position.strategy_id == strategy_id)
        )
        positions = positions_result.scalars().all()

        open_positions = [p for p in positions if p.status == "open"]
        closed_positions = [p for p in positions if p.status == "closed"]

        total_realized_pnl = sum(p.realized_pnl or 0 for p in closed_positions)
        total_unrealized_pnl = sum(p.unrealized_pnl or 0 for p in open_positions)

        total_invested_closed = sum((p.entry_price or 0) * (p.size or 0) for p in closed_positions)
        total_invested_open = sum((p.entry_price or 0) * (p.size or 0) for p in open_positions)

        total_realized_pnl_percent = (
            (total_realized_pnl / total_invested_closed * 100) if total_invested_closed > 0 else 0
        )
        total_unrealized_pnl_percent = (
            (total_unrealized_pnl / total_invested_open * 100) if total_invested_open > 0 else 0
        )

        winning_trades = len([p for p in closed_positions if (p.realized_pnl or 0) > 0])
        win_rate = (winning_trades / len(closed_positions) * 100) if closed_positions else 0

        overviews.append({
            "strategy_id": strategy_id,
            "strategy_name": strategy_name or "Unknown Strategy",
            "total_positions": len(positions),
            "open_positions_count": len(open_positions),
            "closed_positions_count": len(closed_positions),
            "total_realized_pnl": round(total_realized_pnl, 2),
            "total_realized_pnl_percent": round(total_realized_pnl_percent, 2),
            "total_unrealized_pnl": round(total_unrealized_pnl, 2),
            "total_unrealized_pnl_percent": round(total_unrealized_pnl_percent, 2),
            "win_rate": round(win_rate, 2),
            "total_invested": round(total_invested_closed + total_invested_open, 2),
        })

    return overviews


@router.get("/{position_id}", response_model=PositionResponse)
async def get_position(
    position_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get a specific position by ID."""
    result = await db.execute(select(Position).where(Position.id == position_id))
    position = result.scalar_one_or_none()
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    return position
