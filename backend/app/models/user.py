from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from pydantic import BaseModel
from ..database import Base


# SQLAlchemy model
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)


# Pydantic models
class UserResponse(BaseModel):
    id: int
    email: str
    is_active: bool
    is_admin: bool = False

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: str | None = None
