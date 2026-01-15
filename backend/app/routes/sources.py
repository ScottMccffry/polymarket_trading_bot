"""Sources management routes."""
import json
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from ..models.source import Source, SourceCreate, SourceUpdate, SourceResponse
from ..auth.security import get_current_user

router = APIRouter(
    prefix="/api/sources",
    tags=["sources"],
    dependencies=[Depends(get_current_user)]
)


@router.get("", response_model=list[SourceResponse])
async def get_sources(
    type: str | None = None,
    enabled_only: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """Get all sources, optionally filtered by type."""
    query = select(Source)

    if type:
        query = query.where(Source.type == type)
    if enabled_only:
        query = query.where(Source.enabled == True)

    query = query.order_by(Source.created_at.desc())
    result = await db.execute(query)
    sources = result.scalars().all()

    # Parse config JSON for each source
    response = []
    for source in sources:
        config = None
        if source.config:
            try:
                config = json.loads(source.config)
            except json.JSONDecodeError:
                config = {}

        response.append(SourceResponse(
            id=source.id,
            name=source.name,
            type=source.type,
            enabled=source.enabled,
            config=config,
            created_at=source.created_at,
            updated_at=source.updated_at,
        ))

    return response


@router.get("/{source_id}", response_model=SourceResponse)
async def get_source(source_id: int, db: AsyncSession = Depends(get_db)):
    """Get a single source by ID."""
    result = await db.execute(select(Source).where(Source.id == source_id))
    source = result.scalar_one_or_none()

    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    config = None
    if source.config:
        try:
            config = json.loads(source.config)
        except json.JSONDecodeError:
            config = {}

    return SourceResponse(
        id=source.id,
        name=source.name,
        type=source.type,
        enabled=source.enabled,
        config=config,
        created_at=source.created_at,
        updated_at=source.updated_at,
    )


@router.post("", response_model=SourceResponse)
async def create_source(data: SourceCreate, db: AsyncSession = Depends(get_db)):
    """Create a new source."""
    # Validate type
    valid_types = ["telegram", "ifttt", "rss", "manual"]
    if data.type not in valid_types:
        raise HTTPException(status_code=400, detail=f"Invalid type. Must be one of: {valid_types}")

    config_json = json.dumps(data.config) if data.config else None

    source = Source(
        name=data.name,
        type=data.type,
        enabled=data.enabled,
        config=config_json,
    )

    db.add(source)
    await db.commit()
    await db.refresh(source)

    return SourceResponse(
        id=source.id,
        name=source.name,
        type=source.type,
        enabled=source.enabled,
        config=data.config,
        created_at=source.created_at,
        updated_at=source.updated_at,
    )


@router.put("/{source_id}", response_model=SourceResponse)
async def update_source(
    source_id: int,
    data: SourceUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a source."""
    result = await db.execute(select(Source).where(Source.id == source_id))
    source = result.scalar_one_or_none()

    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    if data.name is not None:
        source.name = data.name
    if data.type is not None:
        valid_types = ["telegram", "ifttt", "rss", "manual"]
        if data.type not in valid_types:
            raise HTTPException(status_code=400, detail=f"Invalid type. Must be one of: {valid_types}")
        source.type = data.type
    if data.enabled is not None:
        source.enabled = data.enabled
    if data.config is not None:
        source.config = json.dumps(data.config)

    await db.commit()
    await db.refresh(source)

    config = None
    if source.config:
        try:
            config = json.loads(source.config)
        except json.JSONDecodeError:
            config = {}

    return SourceResponse(
        id=source.id,
        name=source.name,
        type=source.type,
        enabled=source.enabled,
        config=config,
        created_at=source.created_at,
        updated_at=source.updated_at,
    )


@router.delete("/{source_id}")
async def delete_source(source_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a source."""
    result = await db.execute(select(Source).where(Source.id == source_id))
    source = result.scalar_one_or_none()

    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    await db.delete(source)
    await db.commit()

    return {"message": "Source deleted"}


@router.patch("/{source_id}/toggle")
async def toggle_source(source_id: int, db: AsyncSession = Depends(get_db)):
    """Toggle a source's enabled status."""
    result = await db.execute(select(Source).where(Source.id == source_id))
    source = result.scalar_one_or_none()

    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    source.enabled = not source.enabled
    await db.commit()

    return {"id": source_id, "enabled": source.enabled}
