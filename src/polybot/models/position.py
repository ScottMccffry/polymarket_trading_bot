"""Position model for active and closed trades."""

from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import String, Float, ForeignKey, DateTime, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from .base import Base

if TYPE_CHECKING:
    from .signal import Signal


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class PositionStatus(str, Enum):
    """Position lifecycle status."""

    OPEN = "open"
    CLOSED = "closed"
    PARTIAL = "partial"  # Partially closed


class Position(Base):
    """Represents a simulated trading position."""

    __tablename__ = "positions"

    # Primary key
    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # Signal reference
    signal_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("signals.id"),
        index=True,
    )

    # Market info (denormalized for quick access)
    market_id: Mapped[str] = mapped_column(String(255), index=True)
    token_id: Mapped[str] = mapped_column(String(255))
    market_question: Mapped[str] = mapped_column(String(1000))

    # Position details
    side: Mapped[str] = mapped_column(String(10))  # "Yes" or "No"
    strategy: Mapped[str] = mapped_column(String(50), index=True)

    # Pricing
    entry_price: Mapped[float] = mapped_column(Float)
    exit_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    current_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    peak_price: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Size and capital
    size: Mapped[float] = mapped_column(Float)  # Number of shares
    capital_allocated: Mapped[float] = mapped_column(Float)

    # Status and P&L
    status: Mapped[PositionStatus] = mapped_column(
        SQLEnum(PositionStatus),
        default=PositionStatus.OPEN,
        index=True,
    )
    pnl: Mapped[float] = mapped_column(Float, default=0.0)
    unrealized_pnl: Mapped[float] = mapped_column(Float, default=0.0)
    exit_reason: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Source (denormalized)
    source: Mapped[str] = mapped_column(String(255), index=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utc_now, index=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    signal: Mapped["Signal"] = relationship("Signal", back_populates="positions")

    def __repr__(self) -> str:
        return f"<Position {self.id[:8]}... {self.strategy} {self.status.value}>"

    @property
    def is_open(self) -> bool:
        """Check if position is still open."""
        return self.status == PositionStatus.OPEN

    @property
    def hours_open(self) -> float:
        """Get hours since position was opened."""
        end = self.closed_at or datetime.now(timezone.utc)
        return (end - self.created_at).total_seconds() / 3600

    def calculate_pnl(self, current_price: float) -> float:
        """Calculate P&L at a given price."""
        if self.side.lower() == "yes":
            price_diff = current_price - self.entry_price
        else:
            price_diff = self.entry_price - current_price
        return price_diff * self.size

    def calculate_pnl_percent(self, current_price: float) -> float:
        """Calculate P&L percentage at a given price."""
        if self.side.lower() == "yes":
            return (current_price - self.entry_price) / self.entry_price
        else:
            return (self.entry_price - current_price) / self.entry_price
