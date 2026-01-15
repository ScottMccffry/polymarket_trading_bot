import json
from datetime import datetime
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models.market import Market, MarketCreate, MarketUpdate, MarketResponse
from ..models.user import User
from ..auth.security import get_current_user
from ..services.polymarket import MarketHarvester, PolymarketClient
from ..services.qdrant import QdrantService

router = APIRouter(
    prefix="/api/markets",
    tags=["markets"],
    dependencies=[Depends(get_current_user)]  # Require auth for all routes
)


def serialize_market(market: Market) -> dict:
    """Convert Market SQLAlchemy model to response dict"""
    clob_token_ids = []
    if market.clob_token_ids:
        try:
            clob_token_ids = json.loads(market.clob_token_ids)
        except json.JSONDecodeError:
            clob_token_ids = []

    return {
        "condition_id": market.condition_id,
        "question": market.question,
        "description": market.description,
        "market_slug": market.market_slug,
        "end_date_iso": market.end_date_iso,
        "clob_token_ids": clob_token_ids,
        "liquidity": market.liquidity,
        "volume": market.volume,
        "category": market.category,
        "active": bool(market.active),
        "closed": bool(market.closed),
        "created_at": market.created_at,
        "updated_at": market.updated_at,
    }


@router.get("", response_model=list[MarketResponse])
async def get_markets(
    limit: int = 50,
    offset: int = 0,
    search: str | None = None,
    category: str | None = None,
    active: bool | None = None,
    closed: bool | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Get all markets with optional filters"""
    query = select(Market)

    if search:
        query = query.where(Market.question.ilike(f"%{search}%"))

    if category:
        query = query.where(Market.category == category)

    if active is not None:
        query = query.where(Market.active == (1 if active else 0))

    if closed is not None:
        query = query.where(Market.closed == (1 if closed else 0))

    query = query.order_by(Market.volume.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    markets = result.scalars().all()

    return [serialize_market(m) for m in markets]


@router.get("/count")
async def get_markets_count(
    search: str | None = None,
    category: str | None = None,
    active: bool | None = None,
    closed: bool | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Get total count of markets"""
    query = select(func.count()).select_from(Market)

    if search:
        query = query.where(Market.question.ilike(f"%{search}%"))

    if category:
        query = query.where(Market.category == category)

    if active is not None:
        query = query.where(Market.active == (1 if active else 0))

    if closed is not None:
        query = query.where(Market.closed == (1 if closed else 0))

    result = await db.execute(query)
    count = result.scalar()

    return {"count": count}


@router.get("/categories")
async def get_categories(
    db: AsyncSession = Depends(get_db),
):
    """Get all unique categories"""
    query = select(Market.category).where(Market.category.isnot(None)).distinct()
    result = await db.execute(query)
    categories = [row[0] for row in result.all()]

    return {"categories": categories}


@router.get("/search")
async def search_markets(
    q: str = Query(..., description="Search query keywords (comma-separated)"),
    limit: int = Query(20, description="Maximum results"),
    db: AsyncSession = Depends(get_db),
):
    """Search markets by keywords"""
    keywords = [k.strip() for k in q.split(",") if k.strip()]
    if not keywords:
        raise HTTPException(status_code=400, detail="No keywords provided")

    harvester = MarketHarvester()
    markets = await harvester.search(db, keywords=keywords, limit=limit)
    return [serialize_market(m) for m in markets]


@router.get("/price/{token_id}")
async def get_token_price(token_id: str):
    """Get current price for a token from Polymarket"""
    client = PolymarketClient()
    try:
        price = client.get_price(token_id)
        return price
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch price: {str(e)}")


@router.get("/orderbook/{token_id}")
async def get_token_orderbook(token_id: str):
    """Get orderbook for a token from Polymarket"""
    client = PolymarketClient()
    try:
        orderbook = client.get_orderbook(token_id)
        return {"bids": orderbook.bids, "asks": orderbook.asks}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch orderbook: {str(e)}")


@router.get("/price-history/{token_id}")
async def get_price_history(
    token_id: str,
    interval: str = Query("1d", description="Time interval: 1h, 6h, 1d, 1w, max"),
    fidelity: int = Query(60, description="Number of data points"),
):
    """Get price history for a token from Polymarket"""
    client = PolymarketClient()
    try:
        history = client.get_price_history(token_id, interval=interval, fidelity=fidelity)
        return {"token_id": token_id, "interval": interval, "history": history}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch price history: {str(e)}")


@router.get("/semantic-search")
async def semantic_search(
    q: str = Query(..., description="Search query text"),
    limit: int = Query(10, description="Maximum results"),
    score_threshold: float = Query(0.3, description="Minimum similarity score"),
):
    """Search markets by semantic similarity using Qdrant."""
    qdrant = QdrantService()
    if not qdrant.is_configured():
        raise HTTPException(status_code=503, detail="Qdrant not configured")

    results = qdrant.search(query=q, limit=limit, score_threshold=score_threshold)
    return {"query": q, "count": len(results), "results": results}


@router.get("/qdrant/status")
async def qdrant_status():
    """Get Qdrant collection status."""
    qdrant = QdrantService()
    if not qdrant.is_qdrant_configured():
        return {"configured": False, "error": "Qdrant not configured"}

    info = qdrant.get_collection_info()
    return {"configured": True, **info}


@router.get("/{condition_id}", response_model=MarketResponse)
async def get_market(
    condition_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a single market by condition_id"""
    result = await db.execute(
        select(Market).where(Market.condition_id == condition_id)
    )
    market = result.scalar_one_or_none()

    if not market:
        raise HTTPException(status_code=404, detail="Market not found")

    return serialize_market(market)


@router.post("", response_model=MarketResponse)
async def create_market(
    market_data: MarketCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new market"""
    # Check if market already exists
    result = await db.execute(
        select(Market).where(Market.condition_id == market_data.condition_id)
    )
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(status_code=400, detail="Market already exists")

    now = datetime.utcnow().isoformat()
    market = Market(
        condition_id=market_data.condition_id,
        question=market_data.question,
        description=market_data.description,
        market_slug=market_data.market_slug,
        end_date_iso=market_data.end_date_iso,
        clob_token_ids=json.dumps(market_data.clob_token_ids),
        liquidity=market_data.liquidity,
        volume=market_data.volume,
        category=market_data.category,
        active=1 if market_data.active else 0,
        closed=1 if market_data.closed else 0,
        created_at=now,
        updated_at=now,
    )

    db.add(market)
    await db.commit()
    await db.refresh(market)

    return serialize_market(market)


@router.put("/{condition_id}", response_model=MarketResponse)
async def update_market(
    condition_id: str,
    market_data: MarketUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a market"""
    result = await db.execute(
        select(Market).where(Market.condition_id == condition_id)
    )
    market = result.scalar_one_or_none()

    if not market:
        raise HTTPException(status_code=404, detail="Market not found")

    update_data = market_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if field == "clob_token_ids" and value is not None:
            setattr(market, field, json.dumps(value))
        elif field == "active" and value is not None:
            setattr(market, field, 1 if value else 0)
        elif field == "closed" and value is not None:
            setattr(market, field, 1 if value else 0)
        else:
            setattr(market, field, value)

    market.updated_at = datetime.utcnow().isoformat()

    await db.commit()
    await db.refresh(market)

    return serialize_market(market)


@router.delete("/{condition_id}")
async def delete_market(
    condition_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a market"""
    result = await db.execute(
        select(Market).where(Market.condition_id == condition_id)
    )
    market = result.scalar_one_or_none()

    if not market:
        raise HTTPException(status_code=404, detail="Market not found")

    await db.delete(market)
    await db.commit()

    return {"message": "Market deleted successfully"}


@router.delete("")
async def delete_all_markets(
    confirm: bool = Query(False, description="Set to true to confirm deletion"),
    db: AsyncSession = Depends(get_db),
):
    """Delete all markets (requires confirmation)"""
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Set confirm=true to delete all markets"
        )

    result = await db.execute(select(Market))
    markets = result.scalars().all()
    count = len(markets)

    for market in markets:
        await db.delete(market)

    await db.commit()

    return {"message": f"Deleted {count} markets"}


@router.post("/harvest")
async def harvest_markets(
    max_markets: int = Query(5000, description="Maximum number of markets to fetch"),
    db: AsyncSession = Depends(get_db),
):
    """Harvest markets from Polymarket API"""
    harvester = MarketHarvester()
    count = await harvester.harvest(db, max_markets=max_markets)
    return {"message": f"Harvested {count} markets", "count": count}


@router.post("/qdrant/embed")
async def embed_markets(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(5000, description="Maximum markets to embed"),
):
    """Embed all markets in Qdrant for semantic search."""
    qdrant = QdrantService()
    if not qdrant.is_configured():
        raise HTTPException(status_code=503, detail="Qdrant not configured")

    # Fetch markets from DB
    query = select(Market).where(
        Market.active == 1,
        Market.closed == 0,
    ).limit(limit)
    result = await db.execute(query)
    markets = result.scalars().all()

    # Convert to dict format for batch upsert
    market_dicts = [
        {
            "conditionId": m.condition_id,
            "question": m.question,
            "description": m.description,
            "slug": m.market_slug,
            "endDate": m.end_date_iso,
            "liquidity": m.liquidity,
            "volume": m.volume,
        }
        for m in markets
    ]

    count = qdrant.upsert_markets_batch(market_dicts)
    return {"message": f"Embedded {count} markets", "count": count}


@router.delete("/qdrant/clear")
async def clear_qdrant(
    confirm: bool = Query(False, description="Set to true to confirm"),
):
    """Clear all vectors from Qdrant collection."""
    if not confirm:
        raise HTTPException(status_code=400, detail="Set confirm=true to clear")

    qdrant = QdrantService()
    if not qdrant.is_configured():
        raise HTTPException(status_code=503, detail="Qdrant not configured")

    success = qdrant.clear_collection()
    if success:
        return {"message": "Collection cleared"}
    raise HTTPException(status_code=500, detail="Failed to clear collection")
