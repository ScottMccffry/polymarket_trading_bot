from sqlalchemy import String, Float, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column
from pydantic import BaseModel
from ..database import Base


# SQLAlchemy model
class Market(Base):
    __tablename__ = "markets"
    condition_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    market_slug: Mapped[str | None] = mapped_column(String(255), nullable=True)
    end_date_iso: Mapped[str | None] = mapped_column(String(50), nullable=True)
    clob_token_ids: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON array stored as string
    liquidity: Mapped[float] = mapped_column(Float, default=0.0)
    volume: Mapped[float] = mapped_column(Float, default=0.0)
    category: Mapped[str | None] = mapped_column(Text, nullable=True)
    active: Mapped[int] = mapped_column(Integer, default=1)
    closed: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[str | None] = mapped_column(String(50), nullable=True)
    updated_at: Mapped[str | None] = mapped_column(String(50), nullable=True)


# Pydantic models
class MarketCreate(BaseModel):
    condition_id: str
    question: str
    description: str | None = None
    market_slug: str | None = None
    end_date_iso: str | None = None
    clob_token_ids: list[str] = []
    liquidity: float = 0.0
    volume: float = 0.0
    category: str | None = None
    active: bool = True
    closed: bool = False


class MarketUpdate(BaseModel):
    question: str | None = None
    description: str | None = None
    market_slug: str | None = None
    end_date_iso: str | None = None
    clob_token_ids: list[str] | None = None
    liquidity: float | None = None
    volume: float | None = None
    category: str | None = None
    active: bool | None = None
    closed: bool | None = None


class MarketResponse(BaseModel):
    condition_id: str
    question: str
    description: str | None
    market_slug: str | None
    end_date_iso: str | None
    clob_token_ids: list[str]
    liquidity: float
    volume: float
    category: str | None
    active: bool
    closed: bool
    created_at: str | None
    updated_at: str | None
    class Config:
        from_attributes = True
