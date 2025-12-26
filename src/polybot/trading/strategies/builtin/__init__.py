"""Built-in trading strategies."""

from .general import GeneralStrategy
from .conservative import ConservativeStrategy
from .aggressive import AggressiveStrategy
from .trailing import TrailingStopStrategy

__all__ = [
    "GeneralStrategy",
    "ConservativeStrategy",
    "AggressiveStrategy",
    "TrailingStopStrategy",
]
