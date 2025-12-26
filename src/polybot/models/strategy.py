"""Strategy configuration model."""

from datetime import datetime, timezone
from sqlalchemy import String, Float, Boolean, JSON, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class StrategyConfig(Base):
    """Stores strategy configurations (both built-in and custom)."""

    __tablename__ = "strategies"

    # Primary key
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Status
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    is_builtin: Mapped[bool] = mapped_column(Boolean, default=False)

    # Exit parameters (percentages)
    take_profit_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    stop_loss_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    trailing_stop_percent: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Time-based exits
    max_hold_hours: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Partial exits
    partial_exit_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    partial_exit_threshold: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Position sizing
    position_size_multiplier: Mapped[float] = mapped_column(Float, default=1.0)
    max_positions: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Entry filters
    min_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_spread: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Custom rules (DSL expressions or conditions)
    custom_rules: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utc_now, onupdate=_utc_now)

    def __repr__(self) -> str:
        status = "enabled" if self.enabled else "disabled"
        return f"<StrategyConfig {self.name} ({status})>"

    def to_dict(self) -> dict:
        """Convert to dictionary for strategy initialization."""
        return {
            "name": self.name,
            "take_profit_percent": self.take_profit_percent,
            "stop_loss_percent": self.stop_loss_percent,
            "trailing_stop_percent": self.trailing_stop_percent,
            "max_hold_hours": self.max_hold_hours,
            "partial_exit_percent": self.partial_exit_percent,
            "partial_exit_threshold": self.partial_exit_threshold,
            "position_size_multiplier": self.position_size_multiplier,
            "max_positions": self.max_positions,
            "min_confidence": self.min_confidence,
            "max_spread": self.max_spread,
            "custom_rules": self.custom_rules,
        }
