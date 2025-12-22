"""Strategy API routes."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...trading.strategies.registry import StrategyRegistry

router = APIRouter()


class StrategyInfo(BaseModel):
    """Strategy info response."""

    name: str
    description: str
    enabled: bool


class StrategyToggle(BaseModel):
    """Strategy toggle request."""

    enabled: bool


# Global registry instance
_registry: StrategyRegistry | None = None


def get_registry() -> StrategyRegistry:
    """Get the strategy registry singleton."""
    global _registry
    if _registry is None:
        _registry = StrategyRegistry()
    return _registry


@router.get("/", response_model=list[StrategyInfo])
async def list_strategies():
    """List all available strategies."""
    registry = get_registry()
    return [
        StrategyInfo(**s)
        for s in registry.list_strategies()
    ]


@router.get("/{strategy_name}", response_model=StrategyInfo)
async def get_strategy(strategy_name: str):
    """Get a specific strategy."""
    registry = get_registry()
    strategy = registry.get(strategy_name)

    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")

    return StrategyInfo(
        name=strategy.name,
        description=strategy.description,
        enabled=registry.is_enabled(strategy_name),
    )


@router.put("/{strategy_name}/toggle", response_model=StrategyInfo)
async def toggle_strategy(strategy_name: str, body: StrategyToggle):
    """Enable or disable a strategy."""
    registry = get_registry()
    strategy = registry.get(strategy_name)

    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")

    if body.enabled:
        registry.enable(strategy_name)
    else:
        registry.disable(strategy_name)

    return StrategyInfo(
        name=strategy.name,
        description=strategy.description,
        enabled=body.enabled,
    )
