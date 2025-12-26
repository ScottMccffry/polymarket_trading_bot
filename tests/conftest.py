"""Pytest configuration and fixtures."""

import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from polybot.models.base import Base
from polybot.config import Settings


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def db_engine():
    """Create in-memory database engine."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def db_session(db_engine):
    """Create database session."""
    async_session = sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with async_session() as session:
        yield session


@pytest.fixture
def settings():
    """Create test settings."""
    return Settings(
        database_url="sqlite+aiosqlite:///:memory:",
        telegram_api_id=12345,
        telegram_api_hash="test_hash",
        telegram_phone="+1234567890",
        openai_api_key="test_key",
        initial_capital=10000.0,
    )
