"""Simulation state model for paper trading."""

from datetime import datetime, timezone
from sqlalchemy import Integer, Float, DateTime, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class SimulationState(Base):
    """Tracks paper trading portfolio state (single row table)."""

    __tablename__ = "simulation_state"
    __table_args__ = (
        CheckConstraint("id = 1", name="single_row"),
    )

    # Single row constraint
    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)

    # Capital tracking
    total_capital: Mapped[float] = mapped_column(Float, default=10000.0)
    available_capital: Mapped[float] = mapped_column(Float, default=10000.0)
    allocated_capital: Mapped[float] = mapped_column(Float, default=0.0)

    # P&L tracking
    total_pnl: Mapped[float] = mapped_column(Float, default=0.0)
    unrealized_pnl: Mapped[float] = mapped_column(Float, default=0.0)

    # Position counts
    open_positions: Mapped[int] = mapped_column(Integer, default=0)
    closed_positions: Mapped[int] = mapped_column(Integer, default=0)

    # Trade statistics
    winning_trades: Mapped[int] = mapped_column(Integer, default=0)
    losing_trades: Mapped[int] = mapped_column(Integer, default=0)

    # Timestamps
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utc_now, onupdate=_utc_now)

    def __repr__(self) -> str:
        return f"<SimulationState ${self.total_capital:.2f} (${self.available_capital:.2f} available)>"

    @property
    def total_trades(self) -> int:
        """Total number of completed trades."""
        return self.winning_trades + self.losing_trades

    @property
    def win_rate(self) -> float:
        """Win rate as a percentage."""
        if self.total_trades == 0:
            return 0.0
        return self.winning_trades / self.total_trades

    @property
    def portfolio_value(self) -> float:
        """Current total portfolio value."""
        return self.total_capital + self.total_pnl + self.unrealized_pnl

    def can_allocate(self, amount: float) -> bool:
        """Check if we can allocate the given amount."""
        return self.available_capital >= amount

    def allocate(self, amount: float) -> None:
        """Allocate capital for a new position."""
        if not self.can_allocate(amount):
            raise ValueError(f"Insufficient capital: {self.available_capital} < {amount}")
        self.available_capital -= amount
        self.allocated_capital += amount
        self.open_positions += 1

    def release(self, capital: float, pnl: float) -> None:
        """Release capital when closing a position."""
        self.available_capital += capital + pnl
        self.allocated_capital -= capital
        self.total_pnl += pnl
        self.open_positions -= 1
        self.closed_positions += 1

        if pnl > 0:
            self.winning_trades += 1
        elif pnl < 0:
            self.losing_trades += 1
