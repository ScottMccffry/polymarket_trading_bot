from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from ..models.signal import Signal, SignalResponse
from ..auth.security import get_current_user

router = APIRouter(
    prefix="/api/signals",
    tags=["signals"],
    dependencies=[Depends(get_current_user)]
)


@router.get("", response_model=list[SignalResponse])
async def get_signals(
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = 50,
    offset: int = 0,
):
    """Get all signals with pagination."""
    result = await db.execute(
        select(Signal).order_by(Signal.created_at.desc()).offset(offset).limit(limit)
    )
    signals = result.scalars().all()
    return signals


@router.get("/recent", response_model=list[SignalResponse])
async def get_recent_signals(
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = 10,
):
    """Get most recent signals for dashboard."""
    result = await db.execute(
        select(Signal).order_by(Signal.created_at.desc()).limit(limit)
    )
    signals = result.scalars().all()
    return signals


@router.get("/{signal_id}", response_model=SignalResponse)
async def get_signal(
    signal_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get a specific signal by ID."""
    result = await db.execute(select(Signal).where(Signal.signal_id == signal_id))
    signal = result.scalar_one_or_none()
    if not signal:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Signal not found")
    return signal
