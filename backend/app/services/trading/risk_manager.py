"""
Risk Manager - Pre-trade risk validation.

Enforces position sizing, daily loss limits, and drawdown protection.
"""

from dataclasses import dataclass, field


@dataclass
class RiskConfig:
    """Risk management configuration."""
    # Position limits
    max_position_size: float = 100.0  # Max USD per position
    max_portfolio_risk_percent: float = 2.0  # Max % of capital per trade

    # Loss limits
    max_daily_loss: float = 200.0  # Max loss per day in USD
    max_drawdown_percent: float = 10.0  # Max % drawdown from peak

    # Position limits
    max_open_positions: int = 10  # Max concurrent positions

    # Master switch
    enabled: bool = True
