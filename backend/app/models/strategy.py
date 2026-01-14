from sqlalchemy import String, Float, Text, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pydantic import BaseModel
from ..database import Base


# SQLAlchemy models
class CustomStrategy(Base):
    __tablename__ = "custom_strategies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    take_profit: Mapped[float] = mapped_column(Float, nullable=False)
    stop_loss: Mapped[float] = mapped_column(Float, nullable=False)
    trailing_stop: Mapped[float | None] = mapped_column(Float, nullable=True)
    partial_exit_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    partial_exit_threshold: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[str | None] = mapped_column(String(50), nullable=True)


class AdvancedStrategy(Base):
    __tablename__ = "advanced_strategies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Default exit params
    default_take_profit: Mapped[float] = mapped_column(Float, nullable=False)
    default_stop_loss: Mapped[float] = mapped_column(Float, nullable=False)
    default_trailing_stop: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Dynamic trailing stop
    dynamic_trailing_enabled: Mapped[int] = mapped_column(Integer, default=0)
    dynamic_trailing_base: Mapped[float | None] = mapped_column(Float, default=20)
    dynamic_trailing_tight: Mapped[float | None] = mapped_column(Float, default=5)
    dynamic_trailing_threshold: Mapped[float | None] = mapped_column(Float, default=50)

    # Time-based trailing
    time_trailing_enabled: Mapped[int] = mapped_column(Integer, default=0)
    time_trailing_start_hours: Mapped[float | None] = mapped_column(Float, default=24)
    time_trailing_max_hours: Mapped[float | None] = mapped_column(Float, default=72)
    time_trailing_tight: Mapped[float | None] = mapped_column(Float, default=5)

    # Partial exit params
    partial_exit_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    partial_exit_threshold: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Statistical filters
    min_source_win_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    min_source_profit_factor: Mapped[float | None] = mapped_column(Float, nullable=True)
    min_source_trades: Mapped[int | None] = mapped_column(Integer, nullable=True)
    lookback_days: Mapped[int | None] = mapped_column(Integer, default=30)

    enabled: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[str | None] = mapped_column(String(50), nullable=True)
    updated_at: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Relationships
    sources: Mapped[list["AdvancedStrategySource"]] = relationship(
        "AdvancedStrategySource",
        back_populates="strategy",
        lazy="selectin",
        cascade="all, delete-orphan"
    )
    partial_exits: Mapped[list["AdvancedStrategyPartialExit"]] = relationship(
        "AdvancedStrategyPartialExit",
        back_populates="strategy",
        lazy="selectin",
        cascade="all, delete-orphan"
    )


class AdvancedStrategySource(Base):
    __tablename__ = "advanced_strategy_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    strategy_id: Mapped[int] = mapped_column(Integer, ForeignKey("advanced_strategies.id"), nullable=False)
    source: Mapped[str] = mapped_column(String(255), nullable=False)
    take_profit: Mapped[float | None] = mapped_column(Float, nullable=True)
    stop_loss: Mapped[float | None] = mapped_column(Float, nullable=True)
    trailing_stop: Mapped[float | None] = mapped_column(Float, nullable=True)
    position_size_multiplier: Mapped[float | None] = mapped_column(Float, default=1.0)

    # Relationship back to strategy
    strategy: Mapped["AdvancedStrategy"] = relationship("AdvancedStrategy", back_populates="sources")


class AdvancedStrategyPartialExit(Base):
    __tablename__ = "advanced_strategy_partial_exits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    strategy_id: Mapped[int] = mapped_column(Integer, ForeignKey("advanced_strategies.id"), nullable=False)
    exit_order: Mapped[int] = mapped_column(Integer, nullable=False)
    exit_percent: Mapped[float] = mapped_column(Float, nullable=False)
    threshold: Mapped[float] = mapped_column(Float, nullable=False)

    # Relationship back to strategy
    strategy: Mapped["AdvancedStrategy"] = relationship("AdvancedStrategy", back_populates="partial_exits")


# ============ Pydantic Models ============

# Custom Strategy Pydantic Models
class CustomStrategyCreate(BaseModel):
    name: str
    take_profit: float
    stop_loss: float
    trailing_stop: float | None = None
    partial_exit_percent: float | None = None
    partial_exit_threshold: float | None = None


class CustomStrategyUpdate(BaseModel):
    name: str | None = None
    take_profit: float | None = None
    stop_loss: float | None = None
    trailing_stop: float | None = None
    partial_exit_percent: float | None = None
    partial_exit_threshold: float | None = None


class CustomStrategyResponse(BaseModel):
    id: int
    name: str
    take_profit: float
    stop_loss: float
    trailing_stop: float | None
    partial_exit_percent: float | None
    partial_exit_threshold: float | None
    created_at: str | None

    class Config:
        from_attributes = True


# Advanced Strategy Source Pydantic Models
class AdvancedStrategySourceCreate(BaseModel):
    source: str
    take_profit: float | None = None
    stop_loss: float | None = None
    trailing_stop: float | None = None
    position_size_multiplier: float = 1.0


class AdvancedStrategySourceUpdate(BaseModel):
    source: str | None = None
    take_profit: float | None = None
    stop_loss: float | None = None
    trailing_stop: float | None = None
    position_size_multiplier: float | None = None


class AdvancedStrategySourceResponse(BaseModel):
    id: int
    strategy_id: int
    source: str
    take_profit: float | None
    stop_loss: float | None
    trailing_stop: float | None
    position_size_multiplier: float | None

    class Config:
        from_attributes = True


# Advanced Strategy Partial Exit Pydantic Models
class AdvancedStrategyPartialExitCreate(BaseModel):
    exit_order: int
    exit_percent: float
    threshold: float


class AdvancedStrategyPartialExitResponse(BaseModel):
    id: int
    strategy_id: int
    exit_order: int
    exit_percent: float
    threshold: float

    class Config:
        from_attributes = True


# Advanced Strategy Pydantic Models
class AdvancedStrategyCreate(BaseModel):
    name: str
    description: str | None = None

    # Default exit params
    default_take_profit: float
    default_stop_loss: float
    default_trailing_stop: float | None = None

    # Dynamic trailing stop
    dynamic_trailing_enabled: bool = False
    dynamic_trailing_base: float = 20.0
    dynamic_trailing_tight: float = 5.0
    dynamic_trailing_threshold: float = 50.0

    # Time-based trailing
    time_trailing_enabled: bool = False
    time_trailing_start_hours: float = 24.0
    time_trailing_max_hours: float = 72.0
    time_trailing_tight: float = 5.0

    # Partial exit params
    partial_exit_percent: float | None = None
    partial_exit_threshold: float | None = None

    # Statistical filters
    min_source_win_rate: float | None = None
    min_source_profit_factor: float | None = None
    min_source_trades: int | None = None
    lookback_days: int = 30

    enabled: bool = True

    # Nested items (optional on create)
    sources: list[AdvancedStrategySourceCreate] | None = None
    partial_exits: list[AdvancedStrategyPartialExitCreate] | None = None


class AdvancedStrategyUpdate(BaseModel):
    name: str | None = None
    description: str | None = None

    # Default exit params
    default_take_profit: float | None = None
    default_stop_loss: float | None = None
    default_trailing_stop: float | None = None

    # Dynamic trailing stop
    dynamic_trailing_enabled: bool | None = None
    dynamic_trailing_base: float | None = None
    dynamic_trailing_tight: float | None = None
    dynamic_trailing_threshold: float | None = None

    # Time-based trailing
    time_trailing_enabled: bool | None = None
    time_trailing_start_hours: float | None = None
    time_trailing_max_hours: float | None = None
    time_trailing_tight: float | None = None

    # Partial exit params
    partial_exit_percent: float | None = None
    partial_exit_threshold: float | None = None

    # Statistical filters
    min_source_win_rate: float | None = None
    min_source_profit_factor: float | None = None
    min_source_trades: int | None = None
    lookback_days: int | None = None

    enabled: bool | None = None


class AdvancedStrategyResponse(BaseModel):
    id: int
    name: str
    description: str | None

    # Default exit params
    default_take_profit: float
    default_stop_loss: float
    default_trailing_stop: float | None

    # Dynamic trailing stop
    dynamic_trailing_enabled: int
    dynamic_trailing_base: float | None
    dynamic_trailing_tight: float | None
    dynamic_trailing_threshold: float | None

    # Time-based trailing
    time_trailing_enabled: int
    time_trailing_start_hours: float | None
    time_trailing_max_hours: float | None
    time_trailing_tight: float | None

    # Partial exit params
    partial_exit_percent: float | None
    partial_exit_threshold: float | None

    # Statistical filters
    min_source_win_rate: float | None
    min_source_profit_factor: float | None
    min_source_trades: int | None
    lookback_days: int | None

    enabled: int
    created_at: str | None
    updated_at: str | None

    class Config:
        from_attributes = True


class AdvancedStrategyFullResponse(AdvancedStrategyResponse):
    """Full response including sources and partial exits"""
    sources: list[AdvancedStrategySourceResponse] = []
    partial_exits: list[AdvancedStrategyPartialExitResponse] = []
