from sqlalchemy import String, Float, Text
from sqlalchemy.orm import Mapped, mapped_column
from pydantic import BaseModel
from datetime import datetime
from ..database import Base


# SQLAlchemy model
class Signal(Base):
    __tablename__ = "signals"

    signal_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    message_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    keywords: Mapped[str | None] = mapped_column(Text, nullable=True)
    market_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    token_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    market_question: Mapped[str | None] = mapped_column(Text, nullable=True)
    side: Mapped[str | None] = mapped_column(String(50), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    price_at_signal: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[str | None] = mapped_column(String(50), nullable=True)


# Pydantic models
class SignalCreate(BaseModel):
    signal_id: str
    source: str | None = None
    message_text: str | None = None
    keywords: str | None = None
    market_id: str | None = None
    token_id: str | None = None
    market_question: str | None = None
    side: str | None = None
    confidence: float | None = None
    price_at_signal: float | None = None
    created_at: str | None = None


class SignalResponse(BaseModel):
    signal_id: str
    source: str | None
    message_text: str | None
    keywords: str | None
    market_id: str | None
    token_id: str | None
    market_question: str | None
    side: str | None
    confidence: float | None
    price_at_signal: float | None
    created_at: str | None

    class Config:
        from_attributes = True
