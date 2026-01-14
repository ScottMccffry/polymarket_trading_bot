"""Strategy execution service."""
import logging
from datetime import datetime, UTC
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.position import Position
from ...models.strategy import CustomStrategy as CustomStrategyModel, AdvancedStrategy as AdvancedStrategyModel
from ...services.polymarket import PolymarketClient
from .strategies import CustomStrategy, AdvancedStrategy, AdvancedStrategyConfig, SourceParams, PartialExitConfig
from .simulation import SimulationEngine

logger = logging.getLogger(__name__)


class StrategyExecutor:
    """
    Executes trading strategies on open positions.

    Monitors positions and triggers exits based on strategy rules.
    """

    def __init__(self, initial_capital: float = 10000.0):
        self.simulation = SimulationEngine(initial_capital)
        self.polymarket = PolymarketClient()
        self._strategy_cache: dict[int, CustomStrategy | AdvancedStrategy] = {}

    async def load_custom_strategy(self, db: AsyncSession, strategy_id: int) -> CustomStrategy | None:
        """Load a custom strategy from database."""
        if strategy_id in self._strategy_cache:
            cached = self._strategy_cache[strategy_id]
            if isinstance(cached, CustomStrategy):
                return cached

        result = await db.execute(
            select(CustomStrategyModel).where(CustomStrategyModel.id == strategy_id)
        )
        row = result.scalar_one_or_none()

        if not row:
            return None

        strategy = CustomStrategy(
            strategy_id=row.id,
            name=row.name,
            take_profit=row.take_profit,
            stop_loss=row.stop_loss,
            trailing_stop=row.trailing_stop,
            partial_exit_percent=row.partial_exit_percent,
            partial_exit_threshold=row.partial_exit_threshold,
        )
        self._strategy_cache[strategy_id] = strategy
        return strategy

    async def load_advanced_strategy(self, db: AsyncSession, strategy_id: int) -> AdvancedStrategy | None:
        """Load an advanced strategy from database."""
        if strategy_id in self._strategy_cache:
            cached = self._strategy_cache[strategy_id]
            if isinstance(cached, AdvancedStrategy):
                return cached

        result = await db.execute(
            select(AdvancedStrategyModel).where(AdvancedStrategyModel.id == strategy_id)
        )
        row = result.scalar_one_or_none()

        if not row or not row.enabled:
            return None

        # Load sources
        sources = []
        if row.sources:
            for s in row.sources:
                sources.append(SourceParams(
                    source=s.source,
                    take_profit=s.take_profit,
                    stop_loss=s.stop_loss,
                    trailing_stop=s.trailing_stop,
                    position_size_multiplier=s.position_size_multiplier or 1.0,
                ))

        # Load partial exits
        partial_exits = []
        if row.partial_exits:
            for pe in row.partial_exits:
                partial_exits.append(PartialExitConfig(
                    exit_order=pe.exit_order,
                    exit_percent=pe.exit_percent,
                    threshold=pe.threshold,
                ))

        config = AdvancedStrategyConfig(
            id=row.id,
            name=row.name,
            description=row.description,
            default_take_profit=row.default_take_profit,
            default_stop_loss=row.default_stop_loss,
            default_trailing_stop=row.default_trailing_stop,
            dynamic_trailing_enabled=bool(row.dynamic_trailing_enabled),
            dynamic_trailing_base=row.dynamic_trailing_base or 20.0,
            dynamic_trailing_tight=row.dynamic_trailing_tight or 5.0,
            dynamic_trailing_threshold=row.dynamic_trailing_threshold or 50.0,
            time_trailing_enabled=bool(row.time_trailing_enabled),
            time_trailing_start_hours=row.time_trailing_start_hours or 24.0,
            time_trailing_max_hours=row.time_trailing_max_hours or 72.0,
            time_trailing_tight=row.time_trailing_tight or 5.0,
            partial_exit_percent=row.partial_exit_percent,
            partial_exit_threshold=row.partial_exit_threshold,
            min_source_win_rate=row.min_source_win_rate,
            min_source_profit_factor=row.min_source_profit_factor,
            min_source_trades=row.min_source_trades,
            lookback_days=row.lookback_days or 30,
            enabled=bool(row.enabled),
        )

        strategy = AdvancedStrategy(config, sources, partial_exits)
        self._strategy_cache[strategy_id] = strategy
        return strategy

    async def check_position_exits(self, db: AsyncSession) -> list[dict]:
        """
        Check all open positions for exit signals.

        Returns list of exit actions taken.
        """
        # Get all open positions
        result = await db.execute(
            select(Position).where(Position.status == "open")
        )
        positions = list(result.scalars().all())

        if not positions:
            return []

        exits = []

        for position in positions:
            try:
                exit_action = await self._check_single_position(db, position)
                if exit_action:
                    exits.append(exit_action)
            except Exception as e:
                logger.error(f"Error checking position {position.id}: {e}")
                continue

        return exits

    async def _check_single_position(
        self,
        db: AsyncSession,
        position: Position
    ) -> dict | None:
        """Check a single position for exit signal."""
        # Get current price
        if not position.token_id:
            return None

        try:
            price_data = self.polymarket.get_price(position.token_id)
            current_price = float(price_data.get("price", 0))
        except Exception as e:
            logger.warning(f"Could not get price for {position.token_id}: {e}")
            return None

        if current_price <= 0:
            return None

        # Update current price
        position.current_price = current_price

        # Load strategy
        strategy = None
        if position.strategy_id:
            # Try custom strategy first, then advanced
            strategy = await self.load_custom_strategy(db, position.strategy_id)
            if not strategy:
                strategy = await self.load_advanced_strategy(db, position.strategy_id)

        if not strategy:
            # No strategy - skip
            return None

        # Convert position to dict for strategy
        position_dict = {
            "id": position.id,
            "entry_price": position.entry_price,
            "capital_allocated": position.size,
            "size": position.size,
            "side": position.side or "Yes",
            "source": position.source,
            "created_at": position.opened_at,
            "opened_at": position.opened_at,
        }

        # Check for exit
        should_exit, reason, exit_percent = strategy.should_exit(position_dict, current_price)

        if should_exit:
            return await self._execute_exit(
                db, position, current_price, reason, exit_percent
            )

        # Just update unrealized P&L
        entry = position.entry_price or 0
        size = position.size or 0
        if entry > 0 and size > 0:
            pnl = (current_price - entry) * (size / entry)
            position.unrealized_pnl = pnl
            position.unrealized_pnl_percent = (pnl / size) * 100

        await db.commit()
        return None

    async def _execute_exit(
        self,
        db: AsyncSession,
        position: Position,
        exit_price: float,
        reason: str,
        exit_percent: float,
    ) -> dict:
        """Execute position exit."""
        entry = position.entry_price or 0
        size = position.size or 0

        if exit_percent >= 1.0:
            # Full exit
            pnl = (exit_price - entry) * (size / entry) if entry > 0 else 0
            pnl_pct = (pnl / size) * 100 if size > 0 else 0

            position.status = "closed"
            position.exit_price = exit_price
            position.current_price = exit_price
            position.realized_pnl = pnl
            position.realized_pnl_percent = pnl_pct
            position.unrealized_pnl = 0
            position.unrealized_pnl_percent = 0
            position.closed_at = datetime.now(UTC).isoformat()

            await db.commit()

            logger.info(
                f"Closed position {position.id} ({reason}): "
                f"entry={entry:.4f}, exit={exit_price:.4f}, pnl={pnl:.2f} ({pnl_pct:.1f}%)"
            )

            return {
                "position_id": position.id,
                "action": "close",
                "reason": reason,
                "exit_price": exit_price,
                "pnl": pnl,
                "pnl_percent": pnl_pct,
            }
        else:
            # Partial exit
            exit_size = size * exit_percent
            remaining_size = size - exit_size

            pnl = (exit_price - entry) * (exit_size / entry) if entry > 0 else 0

            position.size = remaining_size
            position.realized_pnl = (position.realized_pnl or 0) + pnl

            await db.commit()

            logger.info(
                f"Partial exit position {position.id} ({reason}): "
                f"exited {exit_percent*100:.0f}%, pnl={pnl:.2f}"
            )

            return {
                "position_id": position.id,
                "action": "partial_exit",
                "reason": reason,
                "exit_percent": exit_percent,
                "exit_price": exit_price,
                "pnl": pnl,
                "remaining_size": remaining_size,
            }

    def clear_cache(self):
        """Clear strategy cache."""
        self._strategy_cache.clear()
