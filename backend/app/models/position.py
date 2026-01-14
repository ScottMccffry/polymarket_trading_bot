from sqlalchemy import String, Float, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column
from pydantic import BaseModel
from ..database import Base


# SQLAlchemy model
class Position(Base):
    __tablename__ = "positions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    signal_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    strategy_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    strategy_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    market_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    token_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    market_question: Mapped[str | None] = mapped_column(Text, nullable=True)
    side: Mapped[str | None] = mapped_column(String(50), nullable=True)
    entry_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    current_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    exit_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    size: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="open")  # open, closed
    unrealized_pnl: Mapped[float | None] = mapped_column(Float, nullable=True)
    unrealized_pnl_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    realized_pnl: Mapped[float | None] = mapped_column(Float, nullable=True)
    realized_pnl_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    opened_at: Mapped[str | None] = mapped_column(String(50), nullable=True)
    closed_at: Mapped[str | None] = mapped_column(String(50), nullable=True)


# Pydantic models
class PositionCreate(BaseModel):
    signal_id: str | None = None
    strategy_id: int | None = None
    strategy_name: str | None = None
    market_id: str | None = None
    token_id: str | None = None
    market_question: str | None = None
    side: str | None = None
    entry_price: float | None = None
    size: float | None = None
    source: str | None = None


class PositionResponse(BaseModel):
    id: int
    signal_id: str | None
    strategy_id: int | None
    strategy_name: str | None
    market_id: str | None
    token_id: str | None
    market_question: str | None
    side: str | None
    entry_price: float | None
    current_price: float | None
    exit_price: float | None
    size: float | None
    status: str
    unrealized_pnl: float | None
    unrealized_pnl_percent: float | None
    realized_pnl: float | None
    realized_pnl_percent: float | None
    source: str | None
    opened_at: str | None
    closed_at: str | None

    class Config:
        from_attributes = True


class StrategyOverview(BaseModel):
    strategy_id: int | None
    strategy_name: str
    total_positions: int
    open_positions: int
    closed_positions: int
    total_realized_pnl: float
    total_realized_pnl_percent: float
    total_unrealized_pnl: float
    total_unrealized_pnl_percent: float
    win_rate: float
    total_invested: float
