"""Pytest fixtures for tests."""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.database import Base, get_db
from main import app


# Test database URL (in-memory SQLite)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
test_async_session = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture
async def db_session():
    """Create a fresh database for each test."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with test_async_session() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client(db_session: AsyncSession):
    """Create a test client with overridden database dependency."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def sample_market_data():
    """Sample market data as returned by Polymarket API."""
    return {
        "conditionId": "0x123abc",
        "question": "Will Bitcoin reach $100k by end of 2025?",
        "description": "This market resolves YES if BTC hits $100,000.",
        "slug": "bitcoin-100k-2025",
        "endDate": "2025-12-31T23:59:59Z",
        "clobTokenIds": ["token1", "token2"],
        "liquidity": 50000.0,
        "volume": 100000.0,
        "category": "Crypto",
        "active": True,
        "closed": False,
    }


@pytest.fixture
def sample_orderbook_data():
    """Sample orderbook data."""
    return {
        "bids": [
            {"price": "0.55", "size": "100"},
            {"price": "0.54", "size": "200"},
        ],
        "asks": [
            {"price": "0.56", "size": "150"},
            {"price": "0.57", "size": "250"},
        ],
    }


@pytest.fixture
def sample_price_data():
    """Sample price data."""
    return {"price": "0.55", "spread": "0.01"}
