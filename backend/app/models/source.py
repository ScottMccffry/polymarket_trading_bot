from sqlalchemy import Integer, String, Boolean, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from pydantic import BaseModel
from datetime import datetime
from ..database import Base


# SQLAlchemy model
class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # telegram, ifttt, rss, manual
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    config: Mapped[str] = mapped_column(Text, nullable=True)  # JSON string
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Pydantic models
class SourceCreate(BaseModel):
    name: str
    type: str
    enabled: bool = True
    config: dict | None = None


class SourceUpdate(BaseModel):
    name: str | None = None
    type: str | None = None
    enabled: bool | None = None
    config: dict | None = None


class SourceResponse(BaseModel):
    id: int
    name: str
    type: str
    enabled: bool
    config: dict | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
