from datetime import datetime
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from ..database import get_db
from ..auth.security import get_current_user
from ..models.strategy import (
    CustomStrategy,
    CustomStrategyCreate,
    CustomStrategyUpdate,
    CustomStrategyResponse,
    AdvancedStrategy,
    AdvancedStrategyCreate,
    AdvancedStrategyUpdate,
    AdvancedStrategyResponse,
    AdvancedStrategyFullResponse,
    AdvancedStrategySource,
    AdvancedStrategySourceCreate,
    AdvancedStrategySourceUpdate,
    AdvancedStrategySourceResponse,
    AdvancedStrategyPartialExit,
    AdvancedStrategyPartialExitCreate,
    AdvancedStrategyPartialExitResponse,
)

router = APIRouter(
    prefix="/api/strategies",
    tags=["strategies"],
    dependencies=[Depends(get_current_user)]
)


# ============ Custom Strategies CRUD ============

@router.get("/custom", response_model=list[CustomStrategyResponse])
async def get_custom_strategies(
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get all custom strategies."""
    result = await db.execute(select(CustomStrategy).order_by(CustomStrategy.created_at.desc()))
    strategies = result.scalars().all()
    return strategies


@router.post("/custom", response_model=CustomStrategyResponse)
async def create_custom_strategy(
    strategy: CustomStrategyCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a new custom strategy."""
    # Check if name already exists
    existing = await db.execute(select(CustomStrategy).where(CustomStrategy.name == strategy.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Strategy with this name already exists")

    db_strategy = CustomStrategy(
        **strategy.model_dump(),
        created_at=datetime.utcnow().isoformat(),
    )
    db.add(db_strategy)
    await db.commit()
    await db.refresh(db_strategy)
    return db_strategy


@router.get("/custom/{strategy_id}", response_model=CustomStrategyResponse)
async def get_custom_strategy(
    strategy_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get a specific custom strategy."""
    result = await db.execute(select(CustomStrategy).where(CustomStrategy.id == strategy_id))
    strategy = result.scalar_one_or_none()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return strategy


@router.put("/custom/{strategy_id}", response_model=CustomStrategyResponse)
async def update_custom_strategy(
    strategy_id: int,
    strategy_update: CustomStrategyUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update a custom strategy."""
    result = await db.execute(select(CustomStrategy).where(CustomStrategy.id == strategy_id))
    strategy = result.scalar_one_or_none()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")

    # Check if new name already exists (if name is being updated)
    if strategy_update.name and strategy_update.name != strategy.name:
        existing = await db.execute(select(CustomStrategy).where(CustomStrategy.name == strategy_update.name))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Strategy with this name already exists")

    # Update only provided fields
    update_data = strategy_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(strategy, field, value)

    await db.commit()
    await db.refresh(strategy)
    return strategy


@router.delete("/custom/{strategy_id}")
async def delete_custom_strategy(
    strategy_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete a custom strategy."""
    result = await db.execute(select(CustomStrategy).where(CustomStrategy.id == strategy_id))
    strategy = result.scalar_one_or_none()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    await db.delete(strategy)
    await db.commit()
    return {"message": "Strategy deleted successfully"}


# ============ Advanced Strategies CRUD ============

@router.get("/advanced", response_model=list[AdvancedStrategyResponse])
async def get_advanced_strategies(
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get all advanced strategies."""
    result = await db.execute(select(AdvancedStrategy).order_by(AdvancedStrategy.created_at.desc()))
    strategies = result.scalars().all()
    return strategies


@router.post("/advanced", response_model=AdvancedStrategyFullResponse)
async def create_advanced_strategy(
    strategy: AdvancedStrategyCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a new advanced strategy with optional sources and partial exits."""
    # Check if name already exists
    existing = await db.execute(select(AdvancedStrategy).where(AdvancedStrategy.name == strategy.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Strategy with this name already exists")

    now = datetime.utcnow().isoformat()

    # Create the strategy (excluding nested items)
    strategy_data = strategy.model_dump(exclude={"sources", "partial_exits"})
    strategy_data["dynamic_trailing_enabled"] = int(strategy_data["dynamic_trailing_enabled"])
    strategy_data["time_trailing_enabled"] = int(strategy_data["time_trailing_enabled"])
    strategy_data["enabled"] = int(strategy_data["enabled"])
    strategy_data["created_at"] = now
    strategy_data["updated_at"] = now

    db_strategy = AdvancedStrategy(**strategy_data)
    db.add(db_strategy)
    await db.commit()
    await db.refresh(db_strategy)

    # Create sources if provided
    sources = []
    if strategy.sources:
        for source_data in strategy.sources:
            db_source = AdvancedStrategySource(
                strategy_id=db_strategy.id,
                **source_data.model_dump(),
            )
            db.add(db_source)
            sources.append(db_source)

    # Create partial exits if provided
    partial_exits = []
    if strategy.partial_exits:
        for exit_data in strategy.partial_exits:
            db_exit = AdvancedStrategyPartialExit(
                strategy_id=db_strategy.id,
                **exit_data.model_dump(),
            )
            db.add(db_exit)
            partial_exits.append(db_exit)

    if sources or partial_exits:
        await db.commit()
        for s in sources:
            await db.refresh(s)
        for e in partial_exits:
            await db.refresh(e)

    return AdvancedStrategyFullResponse(
        **{k: v for k, v in db_strategy.__dict__.items() if not k.startswith("_")},
        sources=[AdvancedStrategySourceResponse.model_validate(s) for s in sources],
        partial_exits=[AdvancedStrategyPartialExitResponse.model_validate(e) for e in partial_exits],
    )


@router.get("/advanced/{strategy_id}", response_model=AdvancedStrategyFullResponse)
async def get_advanced_strategy(
    strategy_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get a specific advanced strategy with sources and partial exits."""
    result = await db.execute(select(AdvancedStrategy).where(AdvancedStrategy.id == strategy_id))
    strategy = result.scalar_one_or_none()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")

    # Get sources
    sources_result = await db.execute(
        select(AdvancedStrategySource).where(AdvancedStrategySource.strategy_id == strategy_id)
    )
    sources = sources_result.scalars().all()

    # Get partial exits
    exits_result = await db.execute(
        select(AdvancedStrategyPartialExit)
        .where(AdvancedStrategyPartialExit.strategy_id == strategy_id)
        .order_by(AdvancedStrategyPartialExit.exit_order)
    )
    partial_exits = exits_result.scalars().all()

    return AdvancedStrategyFullResponse(
        **{k: v for k, v in strategy.__dict__.items() if not k.startswith("_")},
        sources=[AdvancedStrategySourceResponse.model_validate(s) for s in sources],
        partial_exits=[AdvancedStrategyPartialExitResponse.model_validate(e) for e in partial_exits],
    )


@router.put("/advanced/{strategy_id}", response_model=AdvancedStrategyResponse)
async def update_advanced_strategy(
    strategy_id: int,
    strategy_update: AdvancedStrategyUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update an advanced strategy."""
    result = await db.execute(select(AdvancedStrategy).where(AdvancedStrategy.id == strategy_id))
    strategy = result.scalar_one_or_none()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")

    # Check if new name already exists
    if strategy_update.name and strategy_update.name != strategy.name:
        existing = await db.execute(select(AdvancedStrategy).where(AdvancedStrategy.name == strategy_update.name))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Strategy with this name already exists")

    # Update only provided fields
    update_data = strategy_update.model_dump(exclude_unset=True)

    # Convert bools to ints for SQLite
    if "dynamic_trailing_enabled" in update_data:
        update_data["dynamic_trailing_enabled"] = int(update_data["dynamic_trailing_enabled"])
    if "time_trailing_enabled" in update_data:
        update_data["time_trailing_enabled"] = int(update_data["time_trailing_enabled"])
    if "enabled" in update_data:
        update_data["enabled"] = int(update_data["enabled"])

    update_data["updated_at"] = datetime.utcnow().isoformat()

    for field, value in update_data.items():
        setattr(strategy, field, value)

    await db.commit()
    await db.refresh(strategy)
    return strategy


@router.delete("/advanced/{strategy_id}")
async def delete_advanced_strategy(
    strategy_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete an advanced strategy and all its sources and partial exits."""
    result = await db.execute(select(AdvancedStrategy).where(AdvancedStrategy.id == strategy_id))
    strategy = result.scalar_one_or_none()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")

    # Delete related sources
    await db.execute(delete(AdvancedStrategySource).where(AdvancedStrategySource.strategy_id == strategy_id))

    # Delete related partial exits
    await db.execute(delete(AdvancedStrategyPartialExit).where(AdvancedStrategyPartialExit.strategy_id == strategy_id))

    # Delete the strategy
    await db.delete(strategy)
    await db.commit()
    return {"message": "Strategy deleted successfully"}


@router.patch("/advanced/{strategy_id}/toggle")
async def toggle_advanced_strategy(
    strategy_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Toggle an advanced strategy's enabled status."""
    result = await db.execute(select(AdvancedStrategy).where(AdvancedStrategy.id == strategy_id))
    strategy = result.scalar_one_or_none()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")

    strategy.enabled = 0 if strategy.enabled else 1
    strategy.updated_at = datetime.utcnow().isoformat()
    await db.commit()
    await db.refresh(strategy)
    return {"enabled": bool(strategy.enabled)}


# ============ Strategy Sources CRUD ============

@router.get("/advanced/{strategy_id}/sources", response_model=list[AdvancedStrategySourceResponse])
async def get_strategy_sources(
    strategy_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get all sources for an advanced strategy."""
    # Verify strategy exists
    strategy_result = await db.execute(select(AdvancedStrategy).where(AdvancedStrategy.id == strategy_id))
    if not strategy_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Strategy not found")

    result = await db.execute(
        select(AdvancedStrategySource).where(AdvancedStrategySource.strategy_id == strategy_id)
    )
    sources = result.scalars().all()
    return sources


@router.post("/advanced/{strategy_id}/sources", response_model=AdvancedStrategySourceResponse)
async def add_strategy_source(
    strategy_id: int,
    source: AdvancedStrategySourceCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Add a source to an advanced strategy."""
    # Verify strategy exists
    strategy_result = await db.execute(select(AdvancedStrategy).where(AdvancedStrategy.id == strategy_id))
    if not strategy_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Strategy not found")

    # Check if source already exists for this strategy
    existing = await db.execute(
        select(AdvancedStrategySource).where(
            AdvancedStrategySource.strategy_id == strategy_id,
            AdvancedStrategySource.source == source.source,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Source already exists for this strategy")

    db_source = AdvancedStrategySource(
        strategy_id=strategy_id,
        **source.model_dump(),
    )
    db.add(db_source)
    await db.commit()
    await db.refresh(db_source)
    return db_source


@router.put("/advanced/{strategy_id}/sources/{source_id}", response_model=AdvancedStrategySourceResponse)
async def update_strategy_source(
    strategy_id: int,
    source_id: int,
    source_update: AdvancedStrategySourceUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update a source for an advanced strategy."""
    result = await db.execute(
        select(AdvancedStrategySource).where(
            AdvancedStrategySource.id == source_id,
            AdvancedStrategySource.strategy_id == strategy_id,
        )
    )
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    update_data = source_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(source, field, value)

    await db.commit()
    await db.refresh(source)
    return source


@router.delete("/advanced/{strategy_id}/sources/{source_id}")
async def delete_strategy_source(
    strategy_id: int,
    source_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete a source from an advanced strategy."""
    result = await db.execute(
        select(AdvancedStrategySource).where(
            AdvancedStrategySource.id == source_id,
            AdvancedStrategySource.strategy_id == strategy_id,
        )
    )
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    await db.delete(source)
    await db.commit()
    return {"message": "Source deleted successfully"}


# ============ Strategy Partial Exits CRUD ============

@router.get("/advanced/{strategy_id}/partial-exits", response_model=list[AdvancedStrategyPartialExitResponse])
async def get_strategy_partial_exits(
    strategy_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get all partial exits for an advanced strategy."""
    # Verify strategy exists
    strategy_result = await db.execute(select(AdvancedStrategy).where(AdvancedStrategy.id == strategy_id))
    if not strategy_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Strategy not found")

    result = await db.execute(
        select(AdvancedStrategyPartialExit)
        .where(AdvancedStrategyPartialExit.strategy_id == strategy_id)
        .order_by(AdvancedStrategyPartialExit.exit_order)
    )
    exits = result.scalars().all()
    return exits


@router.post("/advanced/{strategy_id}/partial-exits", response_model=AdvancedStrategyPartialExitResponse)
async def add_strategy_partial_exit(
    strategy_id: int,
    partial_exit: AdvancedStrategyPartialExitCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Add a partial exit to an advanced strategy."""
    # Verify strategy exists
    strategy_result = await db.execute(select(AdvancedStrategy).where(AdvancedStrategy.id == strategy_id))
    if not strategy_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Strategy not found")

    # Check if exit_order already exists
    existing = await db.execute(
        select(AdvancedStrategyPartialExit).where(
            AdvancedStrategyPartialExit.strategy_id == strategy_id,
            AdvancedStrategyPartialExit.exit_order == partial_exit.exit_order,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Partial exit with this order already exists")

    db_exit = AdvancedStrategyPartialExit(
        strategy_id=strategy_id,
        **partial_exit.model_dump(),
    )
    db.add(db_exit)
    await db.commit()
    await db.refresh(db_exit)
    return db_exit


@router.delete("/advanced/{strategy_id}/partial-exits/{exit_id}")
async def delete_strategy_partial_exit(
    strategy_id: int,
    exit_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete a partial exit from an advanced strategy."""
    result = await db.execute(
        select(AdvancedStrategyPartialExit).where(
            AdvancedStrategyPartialExit.id == exit_id,
            AdvancedStrategyPartialExit.strategy_id == strategy_id,
        )
    )
    partial_exit = result.scalar_one_or_none()
    if not partial_exit:
        raise HTTPException(status_code=404, detail="Partial exit not found")

    await db.delete(partial_exit)
    await db.commit()
    return {"message": "Partial exit deleted successfully"}


# ============ Combined Endpoint ============

@router.get("", response_model=dict)
async def get_all_strategies(
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get all strategies (custom and advanced) for dashboard."""
    custom_result = await db.execute(select(CustomStrategy).order_by(CustomStrategy.created_at.desc()))
    advanced_result = await db.execute(select(AdvancedStrategy).order_by(AdvancedStrategy.created_at.desc()))

    return {
        "custom": custom_result.scalars().all(),
        "advanced": advanced_result.scalars().all(),
    }
