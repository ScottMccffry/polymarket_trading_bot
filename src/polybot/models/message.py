"""Message log model for tracking Telegram messages."""

from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import Integer, String, Text, DateTime, Enum as SQLEnum, BigInteger
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class MessageStatus(str, Enum):
    """Message processing status."""

    RECEIVED = "received"
    PROCESSING = "processing"
    NO_MARKETS = "no_markets"
    NO_SIGNALS = "no_signals"
    TRADED = "traded"
    FILTERED = "filtered"
    ERROR = "error"


class MessageLog(Base):
    """Logs Telegram messages and their processing status."""

    __tablename__ = "message_log"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Telegram identifiers
    message_id: Mapped[int] = mapped_column(BigInteger, index=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, index=True)
    chat_title: Mapped[str] = mapped_column(String(255))
    sender_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    # Message content
    message_text: Mapped[str] = mapped_column(Text)

    # Processing status
    status: Mapped[MessageStatus] = mapped_column(
        SQLEnum(MessageStatus),
        default=MessageStatus.RECEIVED,
        index=True,
    )

    # Processing results
    keywords: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON array
    markets_found: Mapped[int] = mapped_column(Integer, default=0)
    signals_created: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    message_timestamp: Mapped[datetime] = mapped_column(DateTime)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utc_now)

    def __repr__(self) -> str:
        return f"<MessageLog {self.id} from {self.chat_title} ({self.status.value})>"

    @property
    def source(self) -> str:
        """Get source identifier."""
        return f"telegram:{self.chat_title}"
