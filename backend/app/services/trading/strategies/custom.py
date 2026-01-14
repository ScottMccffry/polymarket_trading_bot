"""Custom user-defined exit strategy."""
from .base import ExitStrategy


class CustomStrategy(ExitStrategy):
    """User-defined strategy with configurable parameters."""

    def __init__(
        self,
        strategy_id: int,
        name: str,
        take_profit: float,
        stop_loss: float,
        trailing_stop: float | None = None,
        partial_exit_percent: float | None = None,
        partial_exit_threshold: float | None = None,
    ):
        self.strategy_id = strategy_id
        self.name = name
        self.take_profit = take_profit
        self.stop_loss = stop_loss
        self.trailing_stop = trailing_stop
        self.partial_exit_percent = partial_exit_percent
        self.partial_exit_threshold = partial_exit_threshold
        self._high_water_mark: dict[str, float] = {}

    def should_exit(
        self, position: dict, current_price: float
    ) -> tuple[bool, str, float]:
        """Check if position should be exited based on custom parameters."""
        entry = position["entry_price"]
        capital = position.get("capital_allocated") or position.get("size", 0)
        position_id = str(position.get("id", "default"))
        side = position.get("side", "Yes")

        pnl_pct = self._calc_pnl_percent(entry, current_price, capital, side)

        # Track high water mark for trailing stop
        if position_id not in self._high_water_mark:
            self._high_water_mark[position_id] = pnl_pct
        else:
            self._high_water_mark[position_id] = max(
                self._high_water_mark[position_id], pnl_pct
            )

        # Check take profit
        if pnl_pct >= self.take_profit:
            self._cleanup_position(position_id)
            return True, "take_profit", 1.0

        # Check stop loss
        if pnl_pct <= -self.stop_loss:
            self._cleanup_position(position_id)
            return True, "stop_loss", 1.0

        # Check trailing stop
        if self.trailing_stop:
            high = self._high_water_mark[position_id]
            if high > 0 and (high - pnl_pct) >= self.trailing_stop:
                self._cleanup_position(position_id)
                return True, "trailing_stop", 1.0

        # Check partial exit
        if self.partial_exit_percent and self.partial_exit_threshold:
            if pnl_pct >= self.partial_exit_threshold:
                partial_key = f"{position_id}_partial"
                if partial_key not in self._high_water_mark:
                    self._high_water_mark[partial_key] = True
                    return True, "partial_take_profit", self.partial_exit_percent / 100

        return False, "", 0.0

    def _cleanup_position(self, position_id: str):
        """Clean up tracking state for a closed position."""
        self._high_water_mark.pop(position_id, None)
        self._high_water_mark.pop(f"{position_id}_partial", None)
