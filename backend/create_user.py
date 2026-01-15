#!/usr/bin/env python3
"""
Create a user for login.
Run with: python create_user.py <email> <password>
Or set DEFAULT_ADMIN_EMAIL and DEFAULT_ADMIN_PASSWORD env vars
"""

import asyncio
import sys
import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from app.models.user import User
from app.auth.security import get_password_hash
from app.database import Base
from app.config import get_settings

settings = get_settings()


async def create_user(email: "admin@example.com", password: "admin123"):
    """Create a new user."""
    # Handle database URL conversion for async
    database_url = settings.database_url
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)

    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        # Check if user exists
        result = await session.execute(select(User).where(User.email == email))
        existing = result.scalar_one_or_none()

        if existing:
            print(f"User {email} already exists!")
            return False

        # Create user
        user = User(
            email=email,
            hashed_password=get_password_hash(password),
            is_active=True,
        )
        session.add(user)
        await session.commit()
        print(f"Created user: {email}")
        return True


if __name__ == "__main__":
    asyncio.run(create_user("admin@example.com", "admin123"))
