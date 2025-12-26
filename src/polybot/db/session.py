"""Async database session management."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
import structlog

from ..config import get_settings
from ..models.base import Base

logger = structlog.get_logger()

# Global engine and session factory
_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """Get or create the database engine."""
    global _engine

    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.database_url,
            echo=False,
            pool_pre_ping=True,
            # For SQLite, enable WAL mode
            connect_args={"check_same_thread": False}
            if "sqlite" in settings.database_url
            else {},
        )
        logger.info("database_engine_created", url=settings.database_url)

    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Get or create the session factory."""
    global _session_factory

    if _session_factory is None:
        engine = get_engine()
        _session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
        logger.info("session_factory_created")

    return _session_factory


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get a database session with automatic commit/rollback."""
    factory = get_session_factory()

    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """Initialize the database (create tables)."""
    engine = get_engine()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("database_initialized")


async def close_db() -> None:
    """Close database connections."""
    global _engine, _session_factory

    if _engine:
        await _engine.dispose()
        _engine = None
        _session_factory = None
        logger.info("database_closed")
