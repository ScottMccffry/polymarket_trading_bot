"""Position manager for opening, monitoring, and closing positions."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from ..models.position import Position, PositionStatus
from ..models.signal import Signal
from .simulation import SimulationManager
from .strategies.registry import StrategyRegistry
from .strategies.base import PositionContext, ExitDecision
from ..services.polymarket.client import PolymarketClient
from ..core.events import PositionOpened, PositionClosed, PriceUpdated
from ..core.bus import EventBus
from ..core.exceptions import InsufficientCapitalError

logger = structlog.get_logger()


class PositionManager:
    """Manages trading positions."""

    def __init__(
        self,
        session: AsyncSession,
        event_bus: EventBus,
        strategy_registry: StrategyRegistry,
    ) -> None:
        self.session = session
        self.event_bus = event_bus
        self.strategies = strategy_registry
        self.simulation = SimulationManager(session)
        self.polymarket = PolymarketClient()

    async def open_from_signal(
        self,
        signal: Signal,
        strategy_name: str | None = None,
    ) -> list[Position]:
        """Open position(s) from a signal.

        Args:
            signal: The signal to create positions from
            strategy_name: Specific strategy to use (None = all enabled)

        Returns:
            List of opened positions
        """
        # Get strategies to use
        if strategy_name:
            strategy = self.strategies.get(strategy_name)
            strategies = [strategy] if strategy else []
        else:
            strategies = self.strategies.get_enabled()

        if not strategies:
            logger.warning("no_strategies_available")
            return []

        state = await self.simulation.get_state()
        positions = []

        for strategy in strategies:
            # Check if strategy accepts this signal
            if not strategy.should_enter(
                confidence=signal.confidence,
                spread=0,  # Already checked in signal generation
                price=signal.price_at_signal,
            ):
                continue

            # Calculate position size
            capital_per_strategy = state.available_capital / len(strategies)
            size_capital = strategy.calculate_size(capital_per_strategy, signal.confidence)

            if size_capital <= 0:
                continue

            # Try to allocate capital
            try:
                await self.simulation.allocate_capital(size_capital)
            except InsufficientCapitalError:
                logger.warning(
                    "insufficient_capital",
                    strategy=strategy.name,
                    required=size_capital,
                )
                continue

            # Calculate number of shares
            size = size_capital / signal.price_at_signal

            # Create position
            position = Position(
                id=str(uuid.uuid4()),
                signal_id=signal.id,
                market_id=signal.market_id,
                token_id=signal.token_id,
                market_question=signal.market_question,
                side=signal.side,
                strategy=strategy.name,
                entry_price=signal.price_at_signal,
                size=size,
                capital_allocated=size_capital,
                source=signal.source,
                current_price=signal.price_at_signal,
                peak_price=signal.price_at_signal,
            )

            self.session.add(position)
            positions.append(position)

            # Publish event
            await self.event_bus.publish(PositionOpened(
                position_id=position.id,
                signal_id=signal.id,
                market_id=signal.market_id,
                strategy=strategy.name,
                side=signal.side,
                entry_price=position.entry_price,
                size=size,
                capital=size_capital,
            ))

            logger.info(
                "position_opened",
                position_id=position.id,
                strategy=strategy.name,
                side=signal.side,
                price=position.entry_price,
                size=size,
            )

        await self.session.flush()
        return positions

    async def check_exits(self) -> list[Position]:
        """Check all open positions for exit conditions.

        Returns:
            List of closed positions
        """
        stmt = select(Position).where(Position.status == PositionStatus.OPEN)
        result = await self.session.execute(stmt)
        positions = list(result.scalars().all())

        if not positions:
            return []

        closed = []
        for position in positions:
            # Fetch current price
            try:
                _, ask = await self.polymarket.get_best_prices(position.token_id)
                current_price = ask
            except Exception as e:
                logger.error("price_fetch_error", position_id=position.id, error=str(e))
                continue

            # Update current price and peak
            position.current_price = current_price
            if position.peak_price is None or current_price > position.peak_price:
                position.peak_price = current_price

            # Build context for strategy
            ctx = PositionContext(
                position_id=position.id,
                entry_price=position.entry_price,
                current_price=current_price,
                size=position.size,
                capital_allocated=position.capital_allocated,
                side=position.side,
                peak_price=position.peak_price,
                opened_at=position.created_at,
                hours_open=position.hours_open,
            )

            # Check strategy for exit
            strategy = self.strategies.get(position.strategy)
            if not strategy:
                continue

            decision = strategy.should_exit(ctx)

            if decision.should_exit:
                await self._close_position(position, current_price, decision)
                closed.append(position)
            else:
                # Update unrealized P&L
                position.unrealized_pnl = position.calculate_pnl(current_price)

                await self.event_bus.publish(PriceUpdated(
                    position_id=position.id,
                    price=current_price,
                    pnl=position.unrealized_pnl,
                    pnl_percent=position.calculate_pnl_percent(current_price),
                ))

        await self.session.flush()
        return closed

    async def _close_position(
        self,
        position: Position,
        exit_price: float,
        decision: ExitDecision,
    ) -> None:
        """Close a position."""
        position.status = PositionStatus.CLOSED
        position.exit_price = exit_price
        position.exit_reason = decision.reason
        position.closed_at = datetime.now(timezone.utc)
        position.pnl = position.calculate_pnl(exit_price)
        position.unrealized_pnl = 0.0

        # Release capital
        await self.simulation.release_capital(position.capital_allocated, position.pnl)

        # Publish event
        await self.event_bus.publish(PositionClosed(
            position_id=position.id,
            exit_price=exit_price,
            pnl=position.pnl,
            reason=decision.reason,
        ))

        logger.info(
            "position_closed",
            position_id=position.id,
            strategy=position.strategy,
            reason=decision.reason,
            pnl=position.pnl,
        )

    async def get_open_positions(self) -> list[Position]:
        """Get all open positions."""
        stmt = select(Position).where(Position.status == PositionStatus.OPEN)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_position(self, position_id: str) -> Position | None:
        """Get a position by ID."""
        return await self.session.get(Position, position_id)

    async def close(self) -> None:
        """Clean up resources."""
        await self.polymarket.close()
