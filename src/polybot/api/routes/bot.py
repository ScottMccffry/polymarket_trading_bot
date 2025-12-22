"""Bot control API routes."""

from fastapi import APIRouter
from pydantic import BaseModel

from ...db.session import get_session
from ...models.simulation import SimulationState
from ...trading.simulation import SimulationManager

router = APIRouter()


class SimulationStateResponse(BaseModel):
    """Simulation state response."""

    total_capital: float
    available_capital: float
    allocated_capital: float
    total_pnl: float
    unrealized_pnl: float
    open_positions: int
    closed_positions: int
    win_rate: float
    portfolio_value: float


@router.get("/state", response_model=SimulationStateResponse)
async def get_state():
    """Get current simulation state."""
    async with get_session() as session:
        manager = SimulationManager(session)
        state = await manager.get_state()

        return SimulationStateResponse(
            total_capital=state.total_capital,
            available_capital=state.available_capital,
            allocated_capital=state.allocated_capital,
            total_pnl=state.total_pnl,
            unrealized_pnl=state.unrealized_pnl,
            open_positions=state.open_positions,
            closed_positions=state.closed_positions,
            win_rate=state.win_rate,
            portfolio_value=state.portfolio_value,
        )


@router.post("/reset")
async def reset_simulation():
    """Reset simulation to initial state."""
    async with get_session() as session:
        manager = SimulationManager(session)
        await manager.reset()

    return {"status": "reset", "message": "Simulation reset to initial state"}


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
