"""
Position Manager - Open and manage trading positions.

Supports both paper trading and real order execution via Polymarket CLOB.
"""

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.position import Position
from app.models.signal import Signal
from app.services.polymarket.trading_client import trading_client, OrderSide
from app.services.trading.risk_manager import risk_manager

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
        execute_order: bool = True,
    ) -> Optional[Position]:
        """
        Open a new position based on a signal.

        If live trading is enabled and execute_order=True,
        will place a real order on Polymarket.

        Args:
            db: Database session
            signal: The signal that triggered this position
            strategy_id: Optional strategy ID
            strategy_name: Name of the strategy
            size: Position size in USD (default: 50)
            execute_order: Whether to execute real order if live trading enabled

        Returns:
            The created Position object, or None if risk check fails
        """
        size = size or self.DEFAULT_POSITION_SIZE

        # Run risk validation
        open_positions = await self.get_open_positions(db)
        risk_result = risk_manager.validate_trade(
            size_usd=size,
            capital=10000.0,  # TODO: Get from portfolio tracker
            current_equity=10000.0,  # TODO: Get from portfolio tracker
            peak_equity=10000.0,  # TODO: Get from portfolio tracker
            open_position_count=len(open_positions),
        )

        if not risk_result.can_trade:
            logger.warning(
                f"[POSITION] Risk check failed for signal {signal.signal_id}: "
                f"{', '.join(risk_result.errors)}"
            )
            return None

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

        # Determine trading mode
        is_live = trading_client.is_live_enabled() and execute_order and signal.token_id
        trading_mode = "live" if is_live else "paper"

        # Calculate entry price and shares
        entry_price = signal.price_at_signal or 0.5
        shares = size / entry_price if entry_price > 0 else 0

        # Create position record
        position = Position(
            signal_id=signal.signal_id,
            strategy_id=strategy_id,
            strategy_name=strategy_name,
            market_id=signal.market_id,
            token_id=signal.token_id,
            market_question=signal.market_question,
            side=signal.side,
            entry_price=entry_price,
            current_price=entry_price,
            size=size,
            status="pending" if is_live else "open",
            trading_mode=trading_mode,
            shares_ordered=shares,
            shares_filled=shares if not is_live else 0,  # Paper trades fill instantly
            unrealized_pnl=0.0,
            unrealized_pnl_percent=0.0,
            source=signal.source,
            opened_at=datetime.utcnow().isoformat(),
        )

        db.add(position)
        await db.commit()
        await db.refresh(position)

        # Place real order if live trading
        if is_live:
            await self._execute_entry_order(db, position, entry_price, size)

        logger.info(
            f"[POSITION] Opened {position.side} {trading_mode} position on "
            f"'{position.market_question[:50] if position.market_question else 'Unknown'}...' "
            f"(size=${size}, entry={position.entry_price:.2f})"
        )

        return position

    async def _execute_entry_order(
        self,
        db: AsyncSession,
        position: Position,
        price: float,
        size_usd: float,
    ) -> None:
        """Execute entry order on Polymarket CLOB."""
        # Validate order against limits
        open_positions = await self.get_open_positions(db)
        is_valid, error = trading_client.validate_order(size_usd, len(open_positions))

        if not is_valid:
            position.status = "failed"
            position.last_order_error = error
            position.entry_order_status = "failed"
            await db.commit()
            logger.error(f"[POSITION] Order validation failed: {error}")
            return

        # Place the order
        side = OrderSide.BUY if position.side == "BUY" else OrderSide.SELL
        result = trading_client.place_market_order(
            token_id=position.token_id,
            side=side,
            size_usd=size_usd,
            price=price,
        )

        if result.success:
            position.entry_order_id = result.order_id
            position.entry_order_status = result.status or "pending"
            # For FOK orders, if successful they're filled immediately
            if result.status == "filled" or result.status == "MATCHED":
                position.status = "open"
                position.shares_filled = position.shares_ordered
            logger.info(f"[POSITION] Entry order placed: {result.order_id}")
        else:
            position.status = "failed"
            position.entry_order_status = "failed"
            position.last_order_error = result.error
            logger.error(f"[POSITION] Entry order failed: {result.error}")

        await db.commit()

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
