"""Filtering and grouping utilities for analytics."""
from datetime import datetime
from typing import Sequence
from collections import defaultdict

from ...models.position import Position


class AnalyticsFilter:
    """Filter and group positions for analytics."""

    @staticmethod
    def apply(
        positions: Sequence[Position],
        trading_mode: str | None = None,
        status: str | None = None,
        strategy_name: str | None = None,
        strategy_id: int | None = None,
        source: str | None = None,
        side: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> list[Position]:
        """Apply filters to positions."""
        result = list(positions)

        if trading_mode and trading_mode != "all":
            result = [p for p in result if p.trading_mode == trading_mode]

        if status and status != "all":
            result = [p for p in result if p.status == status]

        if strategy_name:
            result = [p for p in result if p.strategy_name == strategy_name]

        if strategy_id:
            result = [p for p in result if p.strategy_id == strategy_id]

        if source:
            result = [p for p in result if p.source == source]

        if side:
            result = [p for p in result if p.side == side]

        if start_date:
            start_dt = datetime.fromisoformat(start_date)
            result = [
                p for p in result
                if (p.closed_at and datetime.fromisoformat(p.closed_at.replace("Z", "+00:00")).date() >= start_dt.date())
                or (p.opened_at and datetime.fromisoformat(p.opened_at.replace("Z", "+00:00")).date() >= start_dt.date())
            ]

        if end_date:
            end_dt = datetime.fromisoformat(end_date)
            result = [
                p for p in result
                if (p.closed_at and datetime.fromisoformat(p.closed_at.replace("Z", "+00:00")).date() <= end_dt.date())
                or (p.opened_at and datetime.fromisoformat(p.opened_at.replace("Z", "+00:00")).date() <= end_dt.date())
            ]

        return result

    @staticmethod
    def group_by(
        positions: Sequence[Position],
        field: str
    ) -> dict[str, list[Position]]:
        """Group positions by a field value."""
        groups: dict[str, list[Position]] = defaultdict(list)

        for p in positions:
            value = getattr(p, field, None)
            key = str(value) if value is not None else "Unknown"
            groups[key].append(p)

        return dict(groups)

    @staticmethod
    def get_filter_options(positions: Sequence[Position]) -> dict[str, list[str]]:
        """Get available filter options from positions."""
        strategies = set()
        sources = set()
        modes = set()

        for p in positions:
            if p.strategy_name:
                strategies.add(p.strategy_name)
            if p.source:
                sources.add(p.source)
            if p.trading_mode:
                modes.add(p.trading_mode)

        return {
            "strategies": sorted(strategies),
            "sources": sorted(sources),
            "trading_modes": sorted(modes),
        }
