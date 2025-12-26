"""Position API routes."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from ...db.session import get_session
from ...models.position import Position, PositionStatus

router = APIRouter()


class PositionResponse(BaseModel):
    """Position response schema."""

    id: str
    signal_id: str
    market_id: str
    market_question: str
    side: str
    strategy: str
    entry_price: float
    current_price: float | None
    size: float
    capital_allocated: float
    status: str
    pnl: float
    unrealized_pnl: float
    exit_reason: str | None
    source: str
    hours_open: float

    class Config:
        from_attributes = True


@router.get("/", response_model=list[PositionResponse])
async def list_positions(
    status: str | None = None,
    strategy: str | None = None,
    limit: int = 100,
):
    """List positions with optional filters."""
    async with get_session() as session:
        stmt = select(Position).order_by(Position.created_at.desc()).limit(limit)

        if status:
            stmt = stmt.where(Position.status == PositionStatus(status))
        if strategy:
            stmt = stmt.where(Position.strategy == strategy)

        result = await session.execute(stmt)
        positions = result.scalars().all()

        return [
            PositionResponse(
                id=p.id,
                signal_id=p.signal_id,
                market_id=p.market_id,
                market_question=p.market_question,
                side=p.side,
                strategy=p.strategy,
                entry_price=p.entry_price,
                current_price=p.current_price,
                size=p.size,
                capital_allocated=p.capital_allocated,
                status=p.status.value,
                pnl=p.pnl,
                unrealized_pnl=p.unrealized_pnl,
                exit_reason=p.exit_reason,
                source=p.source,
                hours_open=p.hours_open,
            )
            for p in positions
        ]


@router.get("/{position_id}", response_model=PositionResponse)
async def get_position(position_id: str):
    """Get a single position by ID."""
    async with get_session() as session:
        position = await session.get(Position, position_id)

        if not position:
            raise HTTPException(status_code=404, detail="Position not found")

        return PositionResponse(
            id=position.id,
            signal_id=position.signal_id,
            market_id=position.market_id,
            market_question=position.market_question,
            side=position.side,
            strategy=position.strategy,
            entry_price=position.entry_price,
            current_price=position.current_price,
            size=position.size,
            capital_allocated=position.capital_allocated,
            status=position.status.value,
            pnl=position.pnl,
            unrealized_pnl=position.unrealized_pnl,
            exit_reason=position.exit_reason,
            source=position.source,
            hours_open=position.hours_open,
        )


@router.get("/open/summary")
async def open_positions_summary():
    """Get summary of open positions."""
    async with get_session() as session:
        stmt = select(Position).where(Position.status == PositionStatus.OPEN)
        result = await session.execute(stmt)
        positions = list(result.scalars().all())

        total_unrealized = sum(p.unrealized_pnl for p in positions)
        total_capital = sum(p.capital_allocated for p in positions)

        by_strategy = {}
        for p in positions:
            if p.strategy not in by_strategy:
                by_strategy[p.strategy] = {"count": 0, "unrealized_pnl": 0.0}
            by_strategy[p.strategy]["count"] += 1
            by_strategy[p.strategy]["unrealized_pnl"] += p.unrealized_pnl

        return {
            "total_positions": len(positions),
            "total_capital_allocated": total_capital,
            "total_unrealized_pnl": total_unrealized,
            "by_strategy": by_strategy,
        }
