"""Signal API routes."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
from sqlalchemy import select

from ...db.session import get_session
from ...models.signal import Signal

router = APIRouter()


class SignalResponse(BaseModel):
    """Signal response schema."""

    id: str
    market_id: str
    market_question: str
    side: str
    confidence: float
    price_at_signal: float
    source: str
    message_text: str
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/", response_model=list[SignalResponse])
async def list_signals(
    source: str | None = None,
    limit: int = 100,
):
    """List signals with optional filters."""
    async with get_session() as session:
        stmt = select(Signal).order_by(Signal.created_at.desc()).limit(limit)

        if source:
            stmt = stmt.where(Signal.source.contains(source))

        result = await session.execute(stmt)
        signals = result.scalars().all()

        return [
            SignalResponse(
                id=s.id,
                market_id=s.market_id,
                market_question=s.market_question,
                side=s.side,
                confidence=s.confidence,
                price_at_signal=s.price_at_signal,
                source=s.source,
                message_text=s.message_text,
                created_at=s.created_at,
            )
            for s in signals
        ]


@router.get("/{signal_id}", response_model=SignalResponse)
async def get_signal(signal_id: str):
    """Get a single signal by ID."""
    async with get_session() as session:
        signal = await session.get(Signal, signal_id)

        if not signal:
            raise HTTPException(status_code=404, detail="Signal not found")

        return SignalResponse(
            id=signal.id,
            market_id=signal.market_id,
            market_question=signal.market_question,
            side=signal.side,
            confidence=signal.confidence,
            price_at_signal=signal.price_at_signal,
            source=signal.source,
            message_text=signal.message_text,
            created_at=signal.created_at,
        )
