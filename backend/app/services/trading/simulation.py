"""Paper trading simulation state management."""
from datetime import datetime, UTC
from dataclasses import dataclass, field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.position import Position


@dataclass
class SimulationState:
    """Current state of the paper trading simulation."""
    total_capital: float = 10000.0
    available_capital: float = 10000.0
    allocated_capital: float = 0.0
    total_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    open_positions: int = 0
    closed_positions: int = 0


class SimulationEngine:
    """
    Paper trading simulation engine.

    Manages virtual capital allocation and tracks P&L across positions.
    """

    def __init__(self, initial_capital: float = 10000.0):
        self.initial_capital = initial_capital
        self._state: SimulationState | None = None

    async def get_state(self, db: AsyncSession) -> SimulationState:
        """Get current simulation state from positions."""
        # Count open positions
        open_result = await db.execute(
            select(Position).where(Position.status == "open")
        )
        open_positions = list(open_result.scalars().all())

        # Count closed positions
        closed_result = await db.execute(
            select(Position).where(Position.status == "closed")
        )
        closed_positions = list(closed_result.scalars().all())

        # Calculate totals
        allocated = sum(p.size or 0 for p in open_positions)
        unrealized_pnl = sum(p.unrealized_pnl or 0 for p in open_positions)
        realized_pnl = sum(p.realized_pnl or 0 for p in closed_positions)

        total_capital = self.initial_capital + realized_pnl
        available = total_capital - allocated

        return SimulationState(
            total_capital=total_capital,
            available_capital=available,
            allocated_capital=allocated,
            total_pnl=realized_pnl,
            unrealized_pnl=unrealized_pnl,
            open_positions=len(open_positions),
            closed_positions=len(closed_positions),
        )

    async def can_allocate(self, db: AsyncSession, amount: float) -> bool:
        """Check if we have enough capital to allocate."""
        state = await self.get_state(db)
        return state.available_capital >= amount

    async def get_position_size(
        self,
        db: AsyncSession,
        base_size: float,
        multiplier: float = 1.0,
        max_position_pct: float = 10.0,
    ) -> float:
        """
        Calculate position size based on available capital.

        Args:
            db: Database session
            base_size: Base position size requested
            multiplier: Source-specific size multiplier
            max_position_pct: Maximum % of capital per position

        Returns:
            Adjusted position size
        """
        state = await self.get_state(db)

        # Apply multiplier
        size = base_size * multiplier

        # Cap at max position percentage
        max_size = state.available_capital * (max_position_pct / 100)
        size = min(size, max_size)

        # Ensure we have enough capital
        size = min(size, state.available_capital)

        return max(0, size)

    async def update_unrealized_pnl(
        self,
        db: AsyncSession,
        positions: list[Position],
        prices: dict[str, float],
    ) -> float:
        """
        Update unrealized P&L for open positions.

        Args:
            db: Database session
            positions: List of open positions
            prices: Dict of token_id -> current_price

        Returns:
            Total unrealized P&L
        """
        total_unrealized = 0.0

        for position in positions:
            if position.token_id and position.token_id in prices:
                current_price = prices[position.token_id]
                entry_price = position.entry_price or 0
                size = position.size or 0

                if entry_price > 0 and size > 0:
                    # Calculate unrealized P&L
                    pnl = (current_price - entry_price) * (size / entry_price)
                    pnl_pct = (pnl / size) * 100 if size > 0 else 0

                    position.current_price = current_price
                    position.unrealized_pnl = pnl
                    position.unrealized_pnl_percent = pnl_pct

                    total_unrealized += pnl

        await db.commit()
        return total_unrealized

    def reset(self) -> SimulationState:
        """Reset simulation to initial state."""
        return SimulationState(
            total_capital=self.initial_capital,
            available_capital=self.initial_capital,
        )
