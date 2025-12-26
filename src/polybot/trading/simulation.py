"""Simulation state manager for paper trading."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from ..models.simulation import SimulationState
from ..core.exceptions import InsufficientCapitalError
from ..config import get_settings

logger = structlog.get_logger()


class SimulationManager:
    """Manages paper trading simulation state."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.settings = get_settings()

    async def get_state(self) -> SimulationState:
        """Get or create the simulation state."""
        stmt = select(SimulationState).where(SimulationState.id == 1)
        result = await self.session.execute(stmt)
        state = result.scalar_one_or_none()

        if state is None:
            state = SimulationState(
                id=1,
                total_capital=self.settings.initial_capital,
                available_capital=self.settings.initial_capital,
            )
            self.session.add(state)
            await self.session.flush()
            logger.info("simulation_state_created", capital=state.total_capital)

        return state

    async def allocate_capital(self, amount: float) -> None:
        """Allocate capital for a new position.

        Args:
            amount: Amount to allocate

        Raises:
            InsufficientCapitalError: If not enough capital available
        """
        state = await self.get_state()

        if not state.can_allocate(amount):
            raise InsufficientCapitalError(
                f"Insufficient capital: {state.available_capital:.2f} < {amount:.2f}"
            )

        state.allocate(amount)
        logger.debug(
            "capital_allocated",
            amount=amount,
            available=state.available_capital,
        )

    async def release_capital(self, capital: float, pnl: float) -> None:
        """Release capital when closing a position.

        Args:
            capital: Original capital allocated
            pnl: Realized P&L
        """
        state = await self.get_state()
        state.release(capital, pnl)
        logger.debug(
            "capital_released",
            capital=capital,
            pnl=pnl,
            available=state.available_capital,
        )

    async def update_unrealized_pnl(self, unrealized_pnl: float) -> None:
        """Update total unrealized P&L."""
        state = await self.get_state()
        state.unrealized_pnl = unrealized_pnl

    async def reset(self) -> None:
        """Reset simulation to initial state."""
        state = await self.get_state()
        state.total_capital = self.settings.initial_capital
        state.available_capital = self.settings.initial_capital
        state.allocated_capital = 0.0
        state.total_pnl = 0.0
        state.unrealized_pnl = 0.0
        state.open_positions = 0
        state.closed_positions = 0
        state.winning_trades = 0
        state.losing_trades = 0
        logger.info("simulation_reset", capital=state.total_capital)
