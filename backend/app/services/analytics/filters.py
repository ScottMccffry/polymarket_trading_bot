"""Filtering and grouping utilities for analytics."""
from datetime import datetime, date
from typing import Sequence
from collections import defaultdict

from ...models.position import Position


class AnalyticsFilter:
    """Filter and group positions for analytics."""

    @staticmethod
    def _parse_date(date_str: str | None) -> date | None:
        """Parse date string to date object, handling various formats."""
        if not date_str:
            return None
        try:
            # Handle ISO format with timezone (Z suffix)
            normalized = date_str.replace("Z", "+00:00")
            return datetime.fromisoformat(normalized).date()
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _position_matches_date_range(
        position: Position,
        start_date: date | None,
        end_date: date | None,
    ) -> bool:
        """Check if position falls within date range."""
        # Get position date (prefer closed_at, fall back to opened_at)
        pos_date = None
        if position.closed_at:
            pos_date = AnalyticsFilter._parse_date(position.closed_at)
        elif position.opened_at:
            pos_date = AnalyticsFilter._parse_date(position.opened_at)

        if pos_date is None:
            # No valid date - include by default to avoid data loss
            return True

        if start_date and pos_date < start_date:
            return False
        if end_date and pos_date > end_date:
            return False
        return True

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

        # Parse date filters once
        start_dt = AnalyticsFilter._parse_date(start_date)
        end_dt = AnalyticsFilter._parse_date(end_date)

        if start_dt or end_dt:
            result = [
                p for p in result
                if AnalyticsFilter._position_matches_date_range(p, start_dt, end_dt)
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
