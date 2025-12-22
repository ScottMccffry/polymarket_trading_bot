"""Base repository pattern for database operations."""

from typing import Generic, TypeVar, Type, Sequence
from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.base import Base

T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):
    """Base repository with common CRUD operations."""

    def __init__(self, session: AsyncSession, model: Type[T]) -> None:
        self.session = session
        self.model = model

    async def get_by_id(self, id: str | int) -> T | None:
        """Get a single record by ID."""
        return await self.session.get(self.model, id)

    async def get_all(self, limit: int = 100, offset: int = 0) -> Sequence[T]:
        """Get all records with pagination."""
        stmt = select(self.model).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create(self, entity: T) -> T:
        """Create a new record."""
        self.session.add(entity)
        await self.session.flush()
        return entity

    async def create_many(self, entities: list[T]) -> list[T]:
        """Create multiple records."""
        self.session.add_all(entities)
        await self.session.flush()
        return entities

    async def update(self, entity: T) -> T:
        """Update an existing record."""
        await self.session.flush()
        return entity

    async def delete(self, entity: T) -> None:
        """Delete a record."""
        await self.session.delete(entity)
        await self.session.flush()

    async def delete_by_id(self, id: str | int) -> bool:
        """Delete a record by ID."""
        entity = await self.get_by_id(id)
        if entity:
            await self.delete(entity)
            return True
        return False

    async def count(self) -> int:
        """Count all records."""
        stmt = select(func.count()).select_from(self.model)
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def exists(self, id: str | int) -> bool:
        """Check if a record exists."""
        entity = await self.get_by_id(id)
        return entity is not None
