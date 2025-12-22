"""Strategy registry for managing available strategies."""

from typing import Dict
import structlog

from .base import Strategy
from .builtin import (
    GeneralStrategy,
    ConservativeStrategy,
    AggressiveStrategy,
    TrailingStopStrategy,
)

logger = structlog.get_logger()


class StrategyRegistry:
    """Registry for managing trading strategies."""

    def __init__(self) -> None:
        self._strategies: Dict[str, Strategy] = {}
        self._enabled: set[str] = set()
        self._register_builtin()

    def _register_builtin(self) -> None:
        """Register built-in strategies."""
        builtin = [
            GeneralStrategy(),
            ConservativeStrategy(),
            AggressiveStrategy(),
            TrailingStopStrategy(),
        ]

        for strategy in builtin:
            self.register(strategy, enabled=True)

        logger.info("builtin_strategies_registered", count=len(builtin))

    def register(self, strategy: Strategy, enabled: bool = True) -> None:
        """Register a strategy.

        Args:
            strategy: Strategy instance
            enabled: Whether the strategy is enabled by default
        """
        self._strategies[strategy.name] = strategy
        if enabled:
            self._enabled.add(strategy.name)
        logger.debug("strategy_registered", name=strategy.name, enabled=enabled)

    def unregister(self, name: str) -> None:
        """Unregister a strategy by name."""
        if name in self._strategies:
            del self._strategies[name]
            self._enabled.discard(name)

    def get(self, name: str) -> Strategy | None:
        """Get a strategy by name."""
        return self._strategies.get(name)

    def get_all(self) -> list[Strategy]:
        """Get all registered strategies."""
        return list(self._strategies.values())

    def get_enabled(self) -> list[Strategy]:
        """Get all enabled strategies."""
        return [s for s in self._strategies.values() if s.name in self._enabled]

    def enable(self, name: str) -> bool:
        """Enable a strategy."""
        if name in self._strategies:
            self._enabled.add(name)
            return True
        return False

    def disable(self, name: str) -> bool:
        """Disable a strategy."""
        if name in self._enabled:
            self._enabled.discard(name)
            return True
        return False

    def is_enabled(self, name: str) -> bool:
        """Check if a strategy is enabled."""
        return name in self._enabled

    def list_strategies(self) -> list[dict]:
        """List all strategies with their status."""
        return [
            {
                "name": s.name,
                "description": s.description,
                "enabled": s.name in self._enabled,
            }
            for s in self._strategies.values()
        ]
