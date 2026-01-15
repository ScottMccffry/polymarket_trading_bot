"""
Position Manager - Open and manage trading positions.
"""

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.position import Position
from app.models.signal import Signal

logger = logging.getLogger(__name__)


class PositionManager:
    """
    Manages opening and tracking positions.
    """

    DEFAULT_POSITION_SIZE = 50.0  # Default $50 position

    def __init__(self):
        pass

    async def open_position(
        self,
        db: AsyncSession,
        signal: Signal,
        strategy_id: Optional[int] = None,
        strategy_name: str = "signal_trader",
        size: Optional[float] = None,
    ) -> Position:
        """
        Open a new position based on a signal.

        Args:
            db: Database session
            signal: The signal that triggered this position
            strategy_id: Optional strategy ID
            strategy_name: Name of the strategy
            size: Position size in USD (default: 50)

        Returns:
            The created Position object
        """
        size = size or self.DEFAULT_POSITION_SIZE

        # Check for existing open position on same market
        existing = await self._get_existing_position(
            db, signal.market_id, signal.side
        )
        if existing:
            logger.info(
                f"[POSITION] Already have open {existing.side} position on "
                f"market {signal.market_id}"
            )
            return existing

        position = Position(
            signal_id=signal.signal_id,
            strategy_id=strategy_id,
            strategy_name=strategy_name,
            market_id=signal.market_id,
            token_id=signal.token_id,
            market_question=signal.market_question,
            side=signal.side,
            entry_price=signal.price_at_signal or 0.5,  # Default to 0.5 if unknown
            current_price=signal.price_at_signal or 0.5,
            size=size,
            status="open",
            unrealized_pnl=0.0,
            unrealized_pnl_percent=0.0,
            source=signal.source,
            opened_at=datetime.utcnow().isoformat(),
        )

        db.add(position)
        await db.commit()
        await db.refresh(position)

        logger.info(
            f"[POSITION] Opened {position.side} position on "
            f"'{position.market_question[:50] if position.market_question else 'Unknown'}...' "
            f"(size=${size}, entry={position.entry_price:.2f})"
        )

        return position

    async def open_positions_from_signals(
        self,
        db: AsyncSession,
        signals: list[Signal],
        strategy_id: Optional[int] = None,
        strategy_name: str = "signal_trader",
        size_per_position: Optional[float] = None,
    ) -> list[Position]:
        """
        Open positions for multiple signals.

        Args:
            db: Database session
            signals: List of signals to open positions for
            strategy_id: Optional strategy ID
            strategy_name: Name of the strategy
            size_per_position: Position size in USD

        Returns:
            List of created Position objects
        """
        positions = []
        for signal in signals:
            try:
                position = await self.open_position(
                    db=db,
                    signal=signal,
                    strategy_id=strategy_id,
                    strategy_name=strategy_name,
                    size=size_per_position,
                )
                positions.append(position)
            except Exception as e:
                logger.error(f"[POSITION] Failed to open position for {signal.signal_id}: {e}")

        return positions

    async def _get_existing_position(
        self,
        db: AsyncSession,
        market_id: str,
        side: str,
    ) -> Optional[Position]:
        """Check if we already have an open position on this market."""
        if not market_id:
            return None

        result = await db.execute(
            select(Position).where(
                Position.market_id == market_id,
                Position.side == side,
                Position.status == "open",
            )
        )
        return result.scalar_one_or_none()

    async def get_open_positions(
        self,
        db: AsyncSession,
        strategy_name: Optional[str] = None,
    ) -> list[Position]:
        """Get all open positions, optionally filtered by strategy."""
        query = select(Position).where(Position.status == "open")

        if strategy_name:
            query = query.where(Position.strategy_name == strategy_name)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def close_position(
        self,
        db: AsyncSession,
        position_id: int,
        exit_price: float,
    ) -> Position:
        """
        Close a position.

        Args:
            db: Database session
            position_id: ID of position to close
            exit_price: Price at which position is closed

        Returns:
            Updated Position object
        """
        result = await db.execute(
            select(Position).where(Position.id == position_id)
        )
        position = result.scalar_one_or_none()

        if not position:
            raise ValueError(f"Position {position_id} not found")

        if position.status != "open":
            raise ValueError(f"Position {position_id} is not open")

        # Calculate P&L
        entry_price = position.entry_price or 0.5
        size = position.size or self.DEFAULT_POSITION_SIZE

        if position.side == "BUY":
            pnl = (exit_price - entry_price) * size / entry_price
        else:  # SELL
            pnl = (entry_price - exit_price) * size / entry_price

        pnl_percent = (pnl / size) * 100 if size > 0 else 0

        position.exit_price = exit_price
        position.status = "closed"
        position.closed_at = datetime.utcnow().isoformat()
        position.realized_pnl = pnl
        position.realized_pnl_percent = pnl_percent

        await db.commit()
        await db.refresh(position)

        logger.info(
            f"[POSITION] Closed position {position_id}: "
            f"PnL=${pnl:.2f} ({pnl_percent:.1f}%)"
        )

        return position


# Singleton instance
position_manager = PositionManager()
