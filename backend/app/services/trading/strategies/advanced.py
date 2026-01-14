"""Advanced strategy with source filtering and dynamic trailing."""
from datetime import datetime, UTC
from dataclasses import dataclass
from .base import ExitStrategy


@dataclass
class AdvancedStrategyConfig:
    """Configuration for an advanced strategy."""
    id: int
    name: str
    description: str | None

    # Default exit params
    default_take_profit: float
    default_stop_loss: float
    default_trailing_stop: float | None

    # Dynamic trailing (price-based)
    dynamic_trailing_enabled: bool
    dynamic_trailing_base: float
    dynamic_trailing_tight: float
    dynamic_trailing_threshold: float

    # Time-based trailing
    time_trailing_enabled: bool
    time_trailing_start_hours: float
    time_trailing_max_hours: float
    time_trailing_tight: float

    # Partial exit
    partial_exit_percent: float | None
    partial_exit_threshold: float | None

    # Statistical filters
    min_source_win_rate: float | None
    min_source_profit_factor: float | None
    min_source_trades: int | None
    lookback_days: int

    enabled: bool


@dataclass
class PartialExitConfig:
    """Configuration for a partial exit level."""
    exit_order: int
    exit_percent: float  # Percentage of remaining position to exit
    threshold: float  # Profit % threshold to trigger


@dataclass
class SourceParams:
    """Source-specific exit parameters."""
    source: str
    take_profit: float | None
    stop_loss: float | None
    trailing_stop: float | None
    position_size_multiplier: float


class AdvancedStrategy(ExitStrategy):
    """Advanced strategy with source filtering and dynamic trailing stops."""

    def __init__(
        self,
        config: AdvancedStrategyConfig,
        sources: list[SourceParams],
        partial_exits: list[PartialExitConfig] | None = None,
    ):
        self.config = config
        self.strategy_id = config.id
        # Use "advanced_" prefix only if name doesn't already have it
        if config.name.startswith("advanced_"):
            self.name = config.name
        else:
            self.name = f"advanced_{config.name}"
        self.sources = {s.source: s for s in sources}
        # Sort partial exits by threshold (ascending)
        self.partial_exits = sorted(partial_exits or [], key=lambda x: x.threshold)
        self._high_water_mark: dict[str, float] = {}
        self._position_created_at: dict[str, datetime] = {}
        self._partial_exits_fired: dict[str, set[int]] = {}

    def accepts_source(self, source: str) -> bool:
        """Check if this strategy accepts signals from the given source."""
        return source in self.sources

    def get_params_for_source(self, source: str) -> tuple[float, float, float | None]:
        """Get exit parameters for a source (with fallback to defaults)."""
        if source in self.sources:
            s = self.sources[source]
            return (
                s.take_profit if s.take_profit is not None else self.config.default_take_profit,
                s.stop_loss if s.stop_loss is not None else self.config.default_stop_loss,
                s.trailing_stop if s.trailing_stop is not None else self.config.default_trailing_stop,
            )
        return (
            self.config.default_take_profit,
            self.config.default_stop_loss,
            self.config.default_trailing_stop,
        )

    def get_size_multiplier(self, source: str) -> float:
        """Get position size multiplier for a source."""
        if source in self.sources:
            return self.sources[source].position_size_multiplier
        return 1.0

    def _calc_dynamic_trail(
        self, entry_price: float, current_price: float, side: str
    ) -> float:
        """Calculate dynamic trailing stop based on price proximity to max profit."""
        if not self.config.dynamic_trailing_enabled:
            return self.config.dynamic_trailing_base

        # Calculate how much upside has been captured
        if side == "Yes":
            max_upside = 1.0 - entry_price
            if max_upside <= 0:
                return self.config.dynamic_trailing_tight
            upside_captured = current_price - entry_price
            upside_captured_pct = (upside_captured / max_upside) * 100
        else:  # NO position
            max_upside = entry_price
            if max_upside <= 0:
                return self.config.dynamic_trailing_tight
            upside_captured = entry_price - current_price
            upside_captured_pct = (upside_captured / max_upside) * 100

        # Clamp to 0-100
        upside_captured_pct = max(0, min(100, upside_captured_pct))

        # Interpolate trail percentage
        threshold = self.config.dynamic_trailing_threshold
        if upside_captured_pct < threshold:
            return self.config.dynamic_trailing_base
        else:
            # Linear interpolation from base to tight
            progress = (upside_captured_pct - threshold) / (100 - threshold)
            return self.config.dynamic_trailing_base - (
                self.config.dynamic_trailing_base - self.config.dynamic_trailing_tight
            ) * progress

    def _calc_time_trail(self, position_id: str, created_at: datetime | None) -> float:
        """Calculate time-based trailing stop."""
        if not self.config.time_trailing_enabled:
            return self.config.dynamic_trailing_base

        if created_at is None:
            created_at = self._position_created_at.get(position_id)
            if created_at is None:
                return self.config.dynamic_trailing_base

        hold_hours = (datetime.now(UTC) - created_at).total_seconds() / 3600

        start = self.config.time_trailing_start_hours
        max_hours = self.config.time_trailing_max_hours
        base = self.config.dynamic_trailing_base
        tight = self.config.time_trailing_tight

        if hold_hours < start:
            return base
        elif hold_hours >= max_hours:
            return tight
        else:
            progress = (hold_hours - start) / (max_hours - start)
            return base - (base - tight) * progress

    def should_exit(
        self, position: dict, current_price: float
    ) -> tuple[bool, str, float]:
        """Check if position should be exited."""
        entry = position["entry_price"]
        capital = position.get("capital_allocated") or position.get("size", 0)
        position_id = str(position.get("id", "default"))
        side = position.get("side", "Yes")
        source = position.get("source", "")
        created_at = position.get("created_at") or position.get("opened_at")

        # Parse created_at if string
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            except:
                created_at = None

        # Cache created_at for time trailing
        if created_at and position_id not in self._position_created_at:
            self._position_created_at[position_id] = created_at

        # Get exit params for this source
        take_profit, stop_loss, base_trailing = self.get_params_for_source(source)

        # Calculate PnL
        pnl_pct = self._calc_pnl_percent(entry, current_price, capital, side)

        # Track high water mark
        if position_id not in self._high_water_mark:
            self._high_water_mark[position_id] = pnl_pct
        else:
            self._high_water_mark[position_id] = max(
                self._high_water_mark[position_id], pnl_pct
            )

        # Check take profit
        if pnl_pct >= take_profit:
            self._cleanup_position(position_id)
            return True, "take_profit", 1.0

        # Check stop loss
        if pnl_pct <= -stop_loss:
            self._cleanup_position(position_id)
            return True, "stop_loss", 1.0

        # Calculate dynamic trailing stop
        price_trail = self._calc_dynamic_trail(entry, current_price, side)
        time_trail = self._calc_time_trail(position_id, created_at)

        # Use the tighter of the two trailing stops
        effective_trail = min(price_trail, time_trail)

        # Apply trailing stop if in profit
        high = self._high_water_mark[position_id]
        if high > 0 and (high - pnl_pct) >= effective_trail:
            self._cleanup_position(position_id)
            trail_type = "dynamic_trailing" if price_trail <= time_trail else "time_trailing"
            return True, trail_type, 1.0

        # Check multiple partial exits (in order of threshold)
        if self.partial_exits:
            if position_id not in self._partial_exits_fired:
                self._partial_exits_fired[position_id] = set()

            for exit_config in self.partial_exits:
                if exit_config.exit_order in self._partial_exits_fired[position_id]:
                    continue

                if pnl_pct >= exit_config.threshold:
                    self._partial_exits_fired[position_id].add(exit_config.exit_order)
                    return (
                        True,
                        f"partial_take_profit_{exit_config.exit_order}",
                        exit_config.exit_percent / 100,
                    )

        # Fallback: single partial exit from config
        if self.config.partial_exit_percent and self.config.partial_exit_threshold:
            if pnl_pct >= self.config.partial_exit_threshold:
                partial_key = f"{position_id}_partial"
                if partial_key not in self._high_water_mark:
                    self._high_water_mark[partial_key] = True
                    return True, "partial_take_profit", self.config.partial_exit_percent / 100

        return False, "", 0.0

    def _cleanup_position(self, position_id: str):
        """Clean up tracking state for a closed position."""
        self._high_water_mark.pop(position_id, None)
        self._position_created_at.pop(position_id, None)
        self._partial_exits_fired.pop(position_id, None)
