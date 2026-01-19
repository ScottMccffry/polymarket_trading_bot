from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from .config import get_settings

settings = get_settings()

# Convert database URL to async driver format
database_url = settings.database_url
if database_url.startswith("postgresql://"):
    # Railway provides postgresql:// but we need postgresql+asyncpg:// for async
    database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
elif database_url.startswith("postgres://"):
    # Some providers use postgres:// shorthand
    database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)

engine = create_async_engine(database_url, echo=True)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with async_session() as session:
        yield session


from contextlib import asynccontextmanager

@asynccontextmanager
async def get_db_context():
    """
    Context manager for database sessions.

    Usage:
        async with get_db_context() as db:
            result = await db.execute(...)
    """
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Run migrations for new columns
    await run_migrations()


async def run_migrations():
    """Add missing columns to existing tables."""
    from sqlalchemy import text

    # New columns to add to positions table
    position_columns = [
        ("entry_order_id", "VARCHAR(255)"),
        ("entry_order_status", "VARCHAR(50)"),
        ("exit_order_id", "VARCHAR(255)"),
        ("exit_order_status", "VARCHAR(50)"),
        ("shares_ordered", "FLOAT"),
        ("shares_filled", "FLOAT"),
        ("average_fill_price", "FLOAT"),
        ("trading_mode", "VARCHAR(50)"),
        ("last_order_error", "TEXT"),
    ]

    # New column for users table
    user_columns = [
        ("is_admin", "BOOLEAN DEFAULT FALSE"),
    ]

    async with engine.begin() as conn:
        # Add position columns
        for col_name, col_type in position_columns:
            try:
                await conn.execute(text(
                    f"ALTER TABLE positions ADD COLUMN IF NOT EXISTS {col_name} {col_type}"
                ))
            except Exception:
                pass  # Column might already exist or syntax differs

        # Add user columns
        for col_name, col_type in user_columns:
            try:
                await conn.execute(text(
                    f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {col_name} {col_type}"
                ))
            except Exception:
                pass
