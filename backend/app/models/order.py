"""Order model for tracking Polymarket CLOB orders."""

from sqlalchemy import String, Float, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column
from pydantic import BaseModel
from ..database import Base


class Order(Base):
    """SQLAlchemy model for order history tracking."""

    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    position_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    order_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    token_id: Mapped[str] = mapped_column(String(255))
    side: Mapped[str] = mapped_column(String(10))  # BUY, SELL
    order_type: Mapped[str] = mapped_column(String(20))  # GTC, FOK, IOC
    price: Mapped[float] = mapped_column(Float)
    size: Mapped[float] = mapped_column(Float)  # Shares
    filled_size: Mapped[float] = mapped_column(Float, default=0.0)
    average_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(50))  # pending, open, filled, partial, cancelled, failed
    created_at: Mapped[str] = mapped_column(String(50))
    updated_at: Mapped[str | None] = mapped_column(String(50), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)


# Pydantic models
class OrderCreate(BaseModel):
    position_id: int | None = None
    order_id: str
    token_id: str
    side: str
    order_type: str
    price: float
    size: float


class OrderResponse(BaseModel):
    id: int
    position_id: int | None
    order_id: str
    token_id: str
    side: str
    order_type: str
    price: float
    size: float
    filled_size: float
    average_price: float | None
    status: str
    created_at: str
    updated_at: str | None
    error_message: str | None

    class Config:
        from_attributes = True
