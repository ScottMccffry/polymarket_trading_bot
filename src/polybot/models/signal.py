"""Signal model for trading opportunities."""

from datetime import datetime, timezone
from sqlalchemy import String, Float, ForeignKey, JSON, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from .base import Base

if TYPE_CHECKING:
    from .position import Position


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Signal(Base):
    """Represents a trading signal detected from a message."""

    __tablename__ = "signals"

    # Primary key
    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # Market reference
    market_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("markets.condition_id"),
        index=True,
    )
    token_id: Mapped[str] = mapped_column(String(255))
    market_question: Mapped[str] = mapped_column(String(1000))

    # Signal details
    side: Mapped[str] = mapped_column(String(10))  # "Yes" or "No"
    confidence: Mapped[float] = mapped_column(Float)
    price_at_signal: Mapped[float] = mapped_column(Float)

    # Source information
    source: Mapped[str] = mapped_column(String(255), index=True)  # "telegram:GroupName"
    message_text: Mapped[str] = mapped_column(Text)
    keywords: Mapped[list] = mapped_column(JSON, default=list)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utc_now, index=True)

    # Relationships
    positions: Mapped[list["Position"]] = relationship(
        "Position",
        back_populates="signal",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Signal {self.id[:8]}... {self.side}@{self.confidence:.0%}>"

    @property
    def source_type(self) -> str:
        """Get the source type (e.g., 'telegram')."""
        return self.source.split(":")[0] if ":" in self.source else self.source

    @property
    def source_name(self) -> str:
        """Get the source name (e.g., 'GroupName')."""
        return self.source.split(":", 1)[1] if ":" in self.source else self.source
