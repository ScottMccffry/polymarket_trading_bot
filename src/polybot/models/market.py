"""Market model for Polymarket prediction markets."""

from datetime import datetime, timezone
from sqlalchemy import String, Float, Boolean, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Market(Base):
    """Represents a Polymarket prediction market."""

    __tablename__ = "markets"

    # Primary key - Polymarket's condition_id
    condition_id: Mapped[str] = mapped_column(String(255), primary_key=True)

    # Market details
    question: Mapped[str] = mapped_column(String(1000))
    description: Mapped[str | None] = mapped_column(String(5000), nullable=True)
    slug: Mapped[str | None] = mapped_column(String(500), nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Token IDs for CLOB trading [yesTokenId, noTokenId]
    clob_token_ids: Mapped[list] = mapped_column(JSON, default=list)

    # Market metrics
    liquidity: Mapped[float] = mapped_column(Float, default=0.0)
    volume: Mapped[float] = mapped_column(Float, default=0.0)

    # Market status
    end_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    closed: Mapped[bool] = mapped_column(Boolean, default=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utc_now, onupdate=_utc_now)

    def __repr__(self) -> str:
        return f"<Market {self.condition_id[:8]}... '{self.question[:50]}...'>"

    @property
    def yes_token_id(self) -> str | None:
        """Get the YES token ID."""
        if self.clob_token_ids and len(self.clob_token_ids) > 0:
            return self.clob_token_ids[0]
        return None

    @property
    def no_token_id(self) -> str | None:
        """Get the NO token ID."""
        if self.clob_token_ids and len(self.clob_token_ids) > 1:
            return self.clob_token_ids[1]
        return None

    def get_token_id(self, side: str) -> str | None:
        """Get token ID for a given side (Yes/No)."""
        if side.lower() == "yes":
            return self.yes_token_id
        return self.no_token_id
