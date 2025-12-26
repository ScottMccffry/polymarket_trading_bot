"""Trading strategies."""

from .base import Strategy, ExitDecision, PositionContext
from .registry import StrategyRegistry
from .builtin.general import GeneralStrategy
from .builtin.conservative import ConservativeStrategy
from .builtin.aggressive import AggressiveStrategy
from .builtin.trailing import TrailingStopStrategy

__all__ = [
    "Strategy",
    "ExitDecision",
    "PositionContext",
    "StrategyRegistry",
    "GeneralStrategy",
    "ConservativeStrategy",
    "AggressiveStrategy",
    "TrailingStopStrategy",
]
