"""
Order Monitor Service

Monitors pending orders and updates position status when filled.
Runs as a background task to track order execution.
"""

import logging
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.position import Position
from ..polymarket.trading_client import trading_client

logger = logging.getLogger(__name__)


class OrderMonitor:
    """Monitors and updates order statuses for live trading positions."""

    async def check_pending_orders(self, db: AsyncSession) -> list[dict]:
        """
        Check all pending orders and update their status.

        Returns list of status changes.
        """
        if not trading_client.is_live_enabled():
            return []

        # Find positions with pending orders
        result = await db.execute(
            select(Position).where(
                Position.trading_mode == "live",
                Position.status.in_(["pending", "closing"]),
            )
        )
        positions = list(result.scalars().all())

        if not positions:
            return []

        changes = []

        for position in positions:
            try:
                change = await self._check_position_orders(db, position)
                if change:
                    changes.append(change)
            except Exception as e:
                logger.error(f"[ORDER_MONITOR] Error checking position {position.id}: {e}")

        return changes

    async def _check_position_orders(
        self,
        db: AsyncSession,
        position: Position
    ) -> dict | None:
        """Check and update orders for a single position."""

        # Check entry order for pending positions
        if position.status == "pending" and position.entry_order_id:
            result = trading_client.get_order_status(position.entry_order_id)

            if result.success:
                position.entry_order_status = result.status

                if result.status in ["filled", "MATCHED"]:
                    position.status = "open"
                    position.shares_filled = result.filled_size or position.shares_ordered
                    position.average_fill_price = result.average_price
                    # Update entry price to actual fill price
                    if result.average_price:
                        position.entry_price = result.average_price
                    await db.commit()

                    logger.info(
                        f"[ORDER_MONITOR] Entry order filled for position {position.id}: "
                        f"{position.shares_filled:.2f} shares @ {position.average_fill_price or position.entry_price:.4f}"
                    )
                    return {
                        "position_id": position.id,
                        "event": "entry_filled",
                        "shares": position.shares_filled,
                        "price": position.average_fill_price or position.entry_price,
                    }

                elif result.status in ["cancelled", "CANCELLED", "failed", "FAILED", "expired", "EXPIRED"]:
                    position.status = "failed"
                    position.last_order_error = f"Entry order {result.status}"
                    await db.commit()
                    logger.warning(f"[ORDER_MONITOR] Entry order failed for position {position.id}: {result.status}")
                    return {
                        "position_id": position.id,
                        "event": "entry_failed",
                        "status": result.status,
                    }

        # Check exit order for closing positions
        if position.status == "closing" and position.exit_order_id:
            result = trading_client.get_order_status(position.exit_order_id)

            if result.success:
                position.exit_order_status = result.status

                if result.status in ["filled", "MATCHED"]:
                    position.status = "closed"
                    if result.average_price:
                        position.exit_price = result.average_price
                    position.closed_at = datetime.utcnow().isoformat()
                    await db.commit()

                    logger.info(f"[ORDER_MONITOR] Exit order filled for position {position.id}")
                    return {
                        "position_id": position.id,
                        "event": "exit_filled",
                        "price": result.average_price or position.exit_price,
                    }

                elif result.status in ["cancelled", "CANCELLED", "failed", "FAILED", "expired", "EXPIRED"]:
                    # Revert to open status - exit failed
                    position.status = "open"
                    position.exit_order_id = None
                    position.exit_order_status = None
                    position.last_order_error = f"Exit order {result.status}"
                    await db.commit()
                    logger.warning(f"[ORDER_MONITOR] Exit order failed for position {position.id}: {result.status}")
                    return {
                        "position_id": position.id,
                        "event": "exit_failed",
                        "status": result.status,
                    }

        return None


# Singleton instance
order_monitor = OrderMonitor()
