# Polymarket Trading Bot - Complete Rewrite Plan

## Executive Summary

A complete rewrite of the Polymarket paper trading bot with focus on:
- **Event-driven architecture** for clean data flow
- **Modular strategy system** with custom code support
- **Proper async** throughout
- **Type safety** with Pydantic models
- **Database transactions** and connection pooling
- **Comprehensive testing** from day one

---

## Phase 1: Foundation (Core Infrastructure)

### 1.1 Project Setup

**Directory Structure:**
```
polymarket_trading_bot/
├── src/
│   └── polybot/
│       ├── __init__.py
│       ├── main.py              # Entry point
│       ├── config.py            # Pydantic settings
│       │
│       ├── core/
│       │   ├── __init__.py
│       │   ├── events.py        # Event definitions
│       │   ├── bus.py           # Event bus
│       │   └── exceptions.py    # Custom exceptions
│       │
│       ├── models/
│       │   ├── __init__.py
│       │   ├── base.py          # SQLAlchemy base
│       │   ├── market.py        # Market model
│       │   ├── signal.py        # Signal model
│       │   ├── position.py      # Position model
│       │   ├── strategy.py      # Strategy config model
│       │   └── simulation.py    # Paper trading state
│       │
│       ├── db/
│       │   ├── __init__.py
│       │   ├── session.py       # Async session factory
│       │   ├── repository.py    # Base repository
│       │   └── migrations/      # Alembic migrations
│       │
│       ├── services/
│       │   ├── __init__.py
│       │   ├── telegram/
│       │   │   ├── __init__.py
│       │   │   ├── client.py    # Telethon wrapper
│       │   │   └── monitor.py   # Message polling
│       │   ├── polymarket/
│       │   │   ├── __init__.py
│       │   │   ├── client.py    # REST client
│       │   │   ├── harvester.py # Market fetcher
│       │   │   └── orderbook.py # Price fetching
│       │   ├── llm/
│       │   │   ├── __init__.py
│       │   │   ├── client.py    # OpenAI client
│       │   │   ├── analyzer.py  # Market analysis
│       │   │   └── prompts.py   # Prompt templates
│       │   └── qdrant/
│       │       ├── __init__.py
│       │       └── client.py    # Vector search
│       │
│       ├── trading/
│       │   ├── __init__.py
│       │   ├── signals.py       # Signal generator
│       │   ├── positions.py     # Position manager
│       │   ├── simulation.py    # Paper trading state
│       │   └── strategies/
│       │       ├── __init__.py
│       │       ├── base.py      # Strategy protocol
│       │       ├── registry.py  # Strategy registry
│       │       ├── builtin/     # Built-in strategies
│       │       │   ├── general.py
│       │       │   ├── conservative.py
│       │       │   ├── aggressive.py
│       │       │   └── trailing.py
│       │       └── custom/
│       │           ├── __init__.py
│       │           ├── loader.py   # Load from DB/files
│       │           └── executor.py # Safe execution
│       │
│       ├── api/
│       │   ├── __init__.py
│       │   ├── app.py           # FastAPI factory
│       │   ├── deps.py          # Dependencies
│       │   ├── auth.py          # Authentication
│       │   └── routes/
│       │       ├── __init__.py
│       │       ├── dashboard.py
│       │       ├── positions.py
│       │       ├── signals.py
│       │       ├── strategies.py
│       │       ├── markets.py
│       │       └── bot.py
│       │
│       ├── bot/
│       │   ├── __init__.py
│       │   ├── orchestrator.py  # Main coordinator
│       │   └── tasks.py         # Background tasks
│       │
│       └── analytics/
│           ├── __init__.py
│           ├── source.py        # Source performance
│           ├── strategy.py      # Strategy metrics
│           └── impact.py        # Price impact tracking
│
├── templates/                   # Jinja2 templates
│   ├── base.html
│   ├── dashboard.html
│   ├── positions.html
│   ├── strategies.html
│   └── components/
│
├── tests/
│   ├── conftest.py             # Fixtures
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── scripts/
│   ├── run.py                  # Start everything
│   ├── harvest.py              # Fetch markets
│   └── migrate.py              # Run migrations
│
├── pyproject.toml              # Dependencies & config
├── alembic.ini                 # Migrations config
├── .env.example                # Environment template
├── Dockerfile
├── docker-compose.yml
└── README.md
```

**Files to Create:**
- `pyproject.toml` - Dependencies (FastAPI, SQLAlchemy, Telethon, httpx, Pydantic)
- `.env.example` - Environment variable template
- `src/polybot/__init__.py` - Package init
- `src/polybot/config.py` - Pydantic Settings class

### 1.2 Configuration System

```python
# src/polybot/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite+aiosqlite:///./data/polymarket.db"

    # Telegram
    telegram_api_id: int
    telegram_api_hash: str
    telegram_phone: str
    telegram_groups: list[str] = []
    telegram_check_interval: int = 180

    # Polymarket
    polymarket_gamma_url: str = "https://gamma-api.polymarket.com"
    polymarket_clob_url: str = "https://clob.polymarket.com"

    # OpenAI
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"

    # Qdrant
    qdrant_url: str | None = None
    qdrant_api_key: str | None = None
    qdrant_collection: str = "polymarket_markets"

    # Trading
    initial_capital: float = 10000.0
    position_size_percent: float = 0.01
    min_confidence: float = 0.75
    max_spread_percent: float = 15.0
    min_entry_price: float = 0.03
    max_entry_price: float = 0.80

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

### 1.3 Event System

```python
# src/polybot/core/events.py
from dataclasses import dataclass
from datetime import datetime
from typing import Any

@dataclass(frozen=True)
class Event:
    timestamp: datetime = datetime.utcnow()

@dataclass(frozen=True)
class MessageReceived(Event):
    message_id: int
    chat_id: int
    chat_title: str
    text: str
    sender: str

@dataclass(frozen=True)
class SignalCreated(Event):
    signal_id: str
    market_id: str
    side: str
    confidence: float
    source: str

@dataclass(frozen=True)
class PositionOpened(Event):
    position_id: str
    signal_id: str
    strategy: str
    entry_price: float
    size: float

@dataclass(frozen=True)
class PriceUpdated(Event):
    position_id: str
    price: float
    pnl_percent: float

@dataclass(frozen=True)
class PositionClosed(Event):
    position_id: str
    exit_price: float
    pnl: float
    reason: str

@dataclass(frozen=True)
class MarketDataUpdated(Event):
    market_id: str
    token_id: str
    bid: float
    ask: float
    spread: float
```

```python
# src/polybot/core/bus.py
import asyncio
from collections import defaultdict
from typing import Callable, Coroutine, Type
from .events import Event

Handler = Callable[[Event], Coroutine[None, None, None]]

class EventBus:
    def __init__(self):
        self._handlers: dict[Type[Event], list[Handler]] = defaultdict(list)
        self._queue: asyncio.Queue[Event] = asyncio.Queue()
        self._running = False

    def subscribe(self, event_type: Type[Event], handler: Handler):
        self._handlers[event_type].append(handler)

    async def publish(self, event: Event):
        await self._queue.put(event)

    async def start(self):
        self._running = True
        while self._running:
            event = await self._queue.get()
            handlers = self._handlers[type(event)]
            await asyncio.gather(
                *(h(event) for h in handlers),
                return_exceptions=True
            )

    def stop(self):
        self._running = False
```

### 1.4 Database Models (SQLAlchemy Async)

```python
# src/polybot/models/base.py
from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass
from sqlalchemy.ext.asyncio import AsyncAttrs

class Base(AsyncAttrs, MappedAsDataclass, DeclarativeBase):
    pass
```

```python
# src/polybot/models/market.py
from sqlalchemy import String, Float, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from .base import Base

class Market(Base):
    __tablename__ = "markets"

    condition_id: Mapped[str] = mapped_column(String, primary_key=True)
    question: Mapped[str] = mapped_column(String)
    description: Mapped[str | None] = mapped_column(String, default=None)
    slug: Mapped[str | None] = mapped_column(String, default=None)
    end_date: Mapped[datetime | None] = mapped_column(default=None)
    clob_token_ids: Mapped[list] = mapped_column(JSON, default_factory=list)
    liquidity: Mapped[float] = mapped_column(Float, default=0.0)
    volume: Mapped[float] = mapped_column(Float, default=0.0)
    category: Mapped[str | None] = mapped_column(String, default=None)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(default_factory=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default_factory=datetime.utcnow)
```

```python
# src/polybot/models/signal.py
from sqlalchemy import String, Float, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from .base import Base

class Signal(Base):
    __tablename__ = "signals"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    market_id: Mapped[str] = mapped_column(ForeignKey("markets.condition_id"))
    token_id: Mapped[str] = mapped_column(String)
    market_question: Mapped[str] = mapped_column(String)
    side: Mapped[str] = mapped_column(String)  # "Yes" or "No"
    confidence: Mapped[float] = mapped_column(Float)
    price_at_signal: Mapped[float] = mapped_column(Float)
    source: Mapped[str] = mapped_column(String)  # "telegram:GroupName"
    message_text: Mapped[str] = mapped_column(String)
    keywords: Mapped[list] = mapped_column(JSON, default_factory=list)
    created_at: Mapped[datetime] = mapped_column(default_factory=datetime.utcnow)

    # Relationships
    positions: Mapped[list["Position"]] = relationship(back_populates="signal")
```

```python
# src/polybot/models/position.py
from sqlalchemy import String, Float, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from enum import Enum as PyEnum
from .base import Base

class PositionStatus(PyEnum):
    OPEN = "open"
    CLOSED = "closed"
    PARTIAL = "partial"

class Position(Base):
    __tablename__ = "positions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    signal_id: Mapped[str] = mapped_column(ForeignKey("signals.id"))
    market_id: Mapped[str] = mapped_column(String)
    token_id: Mapped[str] = mapped_column(String)
    market_question: Mapped[str] = mapped_column(String)
    side: Mapped[str] = mapped_column(String)
    strategy: Mapped[str] = mapped_column(String)
    entry_price: Mapped[float] = mapped_column(Float)
    exit_price: Mapped[float | None] = mapped_column(Float, default=None)
    size: Mapped[float] = mapped_column(Float)
    capital_allocated: Mapped[float] = mapped_column(Float)
    status: Mapped[PositionStatus] = mapped_column(
        Enum(PositionStatus), default=PositionStatus.OPEN
    )
    pnl: Mapped[float] = mapped_column(Float, default=0.0)
    exit_reason: Mapped[str | None] = mapped_column(String, default=None)
    source: Mapped[str] = mapped_column(String)
    current_price: Mapped[float | None] = mapped_column(Float, default=None)
    unrealized_pnl: Mapped[float] = mapped_column(Float, default=0.0)
    peak_price: Mapped[float | None] = mapped_column(Float, default=None)
    created_at: Mapped[datetime] = mapped_column(default_factory=datetime.utcnow)
    closed_at: Mapped[datetime | None] = mapped_column(default=None)

    # Relationships
    signal: Mapped["Signal"] = relationship(back_populates="positions")
```

```python
# src/polybot/models/strategy.py
from sqlalchemy import String, Float, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from .base import Base

class StrategyConfig(Base):
    __tablename__ = "strategies"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    description: Mapped[str | None] = mapped_column(String, default=None)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    # Core parameters
    take_profit_percent: Mapped[float | None] = mapped_column(Float, default=None)
    stop_loss_percent: Mapped[float | None] = mapped_column(Float, default=None)
    trailing_stop_percent: Mapped[float | None] = mapped_column(Float, default=None)
    max_hold_hours: Mapped[float | None] = mapped_column(Float, default=None)

    # Position sizing
    position_size_multiplier: Mapped[float] = mapped_column(Float, default=1.0)
    max_positions: Mapped[int | None] = mapped_column(default=None)

    # Entry filters
    min_confidence: Mapped[float | None] = mapped_column(Float, default=None)
    max_spread: Mapped[float | None] = mapped_column(Float, default=None)

    # Custom rules (DSL or safe expressions)
    custom_rules: Mapped[dict | None] = mapped_column(JSON, default=None)

    # Metadata
    is_builtin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(default_factory=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default_factory=datetime.utcnow)
```

### 1.5 Database Session Management

```python
# src/polybot/db/session.py
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from contextlib import asynccontextmanager
from ..config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

@asynccontextmanager
async def get_session() -> AsyncSession:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

---

## Phase 2: External Services

### 2.1 Polymarket Client

```python
# src/polybot/services/polymarket/client.py
import httpx
from typing import Any
from ...config import get_settings

class PolymarketClient:
    def __init__(self):
        self.settings = get_settings()
        self._client = httpx.AsyncClient(
            timeout=30.0,
            limits=httpx.Limits(max_connections=10),
        )

    async def get_markets(
        self,
        limit: int = 100,
        offset: int = 0,
        active: bool = True,
    ) -> list[dict[str, Any]]:
        """Fetch markets from Gamma API."""
        response = await self._client.get(
            f"{self.settings.polymarket_gamma_url}/markets",
            params={"limit": limit, "offset": offset, "active": active},
        )
        response.raise_for_status()
        return response.json()

    async def get_orderbook(self, token_id: str) -> dict[str, Any]:
        """Fetch orderbook from CLOB API."""
        response = await self._client.get(
            f"{self.settings.polymarket_clob_url}/book",
            params={"token_id": token_id},
        )
        response.raise_for_status()
        return response.json()

    async def get_best_price(self, token_id: str) -> tuple[float, float]:
        """Get best bid and ask prices."""
        book = await self.get_orderbook(token_id)
        bids = book.get("bids", [])
        asks = book.get("asks", [])

        best_bid = float(bids[0]["price"]) if bids else 0.0
        best_ask = float(asks[0]["price"]) if asks else 1.0

        return best_bid, best_ask

    async def close(self):
        await self._client.aclose()
```

### 2.2 Telegram Monitor

```python
# src/polybot/services/telegram/monitor.py
import asyncio
from telethon import TelegramClient
from telethon.tl.types import Message
from ...core.events import MessageReceived
from ...core.bus import EventBus
from ...config import get_settings

class TelegramMonitor:
    def __init__(self, event_bus: EventBus):
        self.settings = get_settings()
        self.event_bus = event_bus
        self.client = TelegramClient(
            "data/telegram",
            self.settings.telegram_api_id,
            self.settings.telegram_api_hash,
        )
        self._last_message_ids: dict[int, int] = {}
        self._running = False

    async def start(self):
        await self.client.start(phone=self.settings.telegram_phone)
        self._running = True

        # Initial swipe - get last 3 messages from each group
        for group_name in self.settings.telegram_groups:
            await self._initial_swipe(group_name)

        # Start polling loop
        asyncio.create_task(self._poll_loop())

    async def _initial_swipe(self, group_name: str):
        """Fetch last 3 messages on startup."""
        try:
            entity = await self.client.get_entity(group_name)
            messages = await self.client.get_messages(entity, limit=3)
            for msg in reversed(messages):
                if msg.text:
                    self._last_message_ids[entity.id] = msg.id
                    await self._process_message(msg, entity.title)
        except Exception as e:
            print(f"Error in initial swipe for {group_name}: {e}")

    async def _poll_loop(self):
        while self._running:
            for group_name in self.settings.telegram_groups:
                await self._check_group(group_name)
            await asyncio.sleep(self.settings.telegram_check_interval)

    async def _check_group(self, group_name: str):
        try:
            entity = await self.client.get_entity(group_name)
            last_id = self._last_message_ids.get(entity.id, 0)
            messages = await self.client.get_messages(
                entity, min_id=last_id, limit=50
            )
            for msg in reversed(messages):
                if msg.text and msg.id > last_id:
                    self._last_message_ids[entity.id] = msg.id
                    await self._process_message(msg, entity.title)
        except Exception as e:
            print(f"Error checking {group_name}: {e}")

    async def _process_message(self, msg: Message, chat_title: str):
        event = MessageReceived(
            message_id=msg.id,
            chat_id=msg.chat_id,
            chat_title=chat_title,
            text=msg.text,
            sender=str(msg.sender_id),
        )
        await self.event_bus.publish(event)

    async def stop(self):
        self._running = False
        await self.client.disconnect()
```

### 2.3 LLM Analyzer

```python
# src/polybot/services/llm/analyzer.py
from openai import AsyncOpenAI
from pydantic import BaseModel
from ...config import get_settings

class MarketAnalysis(BaseModel):
    is_relevant: bool
    side: str  # "Yes" or "No"
    confidence: float
    reasoning: str

class LLMAnalyzer:
    def __init__(self):
        self.settings = get_settings()
        self.client = AsyncOpenAI(api_key=self.settings.openai_api_key)

    async def analyze_market(
        self,
        message_text: str,
        market_question: str,
        market_description: str | None = None,
    ) -> MarketAnalysis:
        """Analyze if message is relevant to market and predict direction."""

        prompt = f"""Analyze if this message is relevant to the prediction market and predict the outcome.

Message: {message_text}

Market Question: {market_question}
{f"Description: {market_description}" if market_description else ""}

Respond with JSON:
{{
    "is_relevant": true/false,
    "side": "Yes" or "No" (which outcome does the message suggest),
    "confidence": 0.0-1.0 (how confident are you),
    "reasoning": "brief explanation"
}}
"""

        response = await self.client.chat.completions.create(
            model=self.settings.openai_model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.2,
        )

        import json
        data = json.loads(response.choices[0].message.content)
        return MarketAnalysis(**data)

    async def extract_keywords(self, text: str) -> list[str]:
        """Extract searchable keywords from message."""
        prompt = f"""Extract 3-5 search keywords from this message for finding relevant prediction markets.
Return only the keywords as a JSON array.

Message: {text}
"""
        response = await self.client.chat.completions.create(
            model=self.settings.openai_model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.1,
        )

        import json
        data = json.loads(response.choices[0].message.content)
        return data.get("keywords", [])
```

### 2.4 Qdrant Client (RAG)

```python
# src/polybot/services/qdrant/client.py
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from openai import AsyncOpenAI
import hashlib
from ...config import get_settings

class QdrantService:
    def __init__(self):
        self.settings = get_settings()
        self.client = AsyncQdrantClient(
            url=self.settings.qdrant_url,
            api_key=self.settings.qdrant_api_key,
        ) if self.settings.qdrant_url else None
        self.openai = AsyncOpenAI(api_key=self.settings.openai_api_key)
        self.collection = self.settings.qdrant_collection
        self.dimension = 1536  # text-embedding-3-small

    async def ensure_collection(self):
        if not self.client:
            return
        collections = await self.client.get_collections()
        if self.collection not in [c.name for c in collections.collections]:
            await self.client.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(
                    size=self.dimension,
                    distance=Distance.COSINE,
                ),
            )

    async def embed_text(self, text: str) -> list[float]:
        response = await self.openai.embeddings.create(
            model=self.settings.openai_embedding_model,
            input=text,
        )
        return response.data[0].embedding

    async def upsert_markets(self, markets: list[dict]):
        if not self.client:
            return

        points = []
        for market in markets:
            text = f"{market['question']} {market.get('description', '')}"
            vector = await self.embed_text(text)
            point_id = hashlib.md5(market["condition_id"].encode()).hexdigest()
            points.append(PointStruct(
                id=point_id,
                vector=vector,
                payload=market,
            ))

        await self.client.upsert(
            collection_name=self.collection,
            points=points,
        )

    async def search(self, query: str, limit: int = 10) -> list[dict]:
        if not self.client:
            return []

        vector = await self.embed_text(query)
        results = await self.client.search(
            collection_name=self.collection,
            query_vector=vector,
            limit=limit,
            score_threshold=0.35,
        )
        return [r.payload for r in results]
```

---

## Phase 3: Trading Core

### 3.1 Strategy System

```python
# src/polybot/trading/strategies/base.py
from typing import Protocol, NamedTuple
from datetime import datetime

class ExitDecision(NamedTuple):
    should_exit: bool
    reason: str
    exit_percent: float  # 1.0 = full exit, 0.5 = half

class PositionContext(NamedTuple):
    position_id: str
    entry_price: float
    current_price: float
    size: float
    capital_allocated: float
    side: str  # "Yes" or "No"
    peak_price: float | None
    opened_at: datetime
    hours_open: float

class Strategy(Protocol):
    name: str

    def should_enter(
        self,
        confidence: float,
        spread: float,
        price: float,
    ) -> bool:
        """Determine if strategy should take this signal."""
        ...

    def should_exit(self, ctx: PositionContext) -> ExitDecision:
        """Determine if position should be exited."""
        ...

    def calculate_size(
        self,
        available_capital: float,
        confidence: float,
    ) -> float:
        """Calculate position size."""
        ...
```

```python
# src/polybot/trading/strategies/builtin/general.py
from ..base import Strategy, ExitDecision, PositionContext
from ....config import get_settings

class GeneralStrategy:
    name = "general"
    take_profit = 0.50  # 50%
    stop_loss = -0.25   # -25%

    def __init__(self):
        self.settings = get_settings()

    def should_enter(
        self,
        confidence: float,
        spread: float,
        price: float,
    ) -> bool:
        return (
            confidence >= self.settings.min_confidence
            and spread <= self.settings.max_spread_percent
            and self.settings.min_entry_price <= price <= self.settings.max_entry_price
        )

    def should_exit(self, ctx: PositionContext) -> ExitDecision:
        pnl_pct = self._calc_pnl_percent(ctx)

        if pnl_pct >= self.take_profit:
            return ExitDecision(True, "take_profit", 1.0)
        if pnl_pct <= self.stop_loss:
            return ExitDecision(True, "stop_loss", 1.0)

        return ExitDecision(False, "", 0.0)

    def calculate_size(
        self,
        available_capital: float,
        confidence: float,
    ) -> float:
        base_size = available_capital * self.settings.position_size_percent
        return base_size * confidence

    def _calc_pnl_percent(self, ctx: PositionContext) -> float:
        if ctx.side == "Yes":
            return (ctx.current_price - ctx.entry_price) / ctx.entry_price
        else:
            return (ctx.entry_price - ctx.current_price) / ctx.entry_price
```

```python
# src/polybot/trading/strategies/registry.py
from typing import Dict
from .base import Strategy
from .builtin.general import GeneralStrategy
from .builtin.conservative import ConservativeStrategy
from .builtin.aggressive import AggressiveStrategy
from .builtin.trailing import TrailingStopStrategy

class StrategyRegistry:
    def __init__(self):
        self._strategies: Dict[str, Strategy] = {}
        self._register_builtin()

    def _register_builtin(self):
        for cls in [GeneralStrategy, ConservativeStrategy,
                    AggressiveStrategy, TrailingStopStrategy]:
            strategy = cls()
            self._strategies[strategy.name] = strategy

    def register(self, strategy: Strategy):
        self._strategies[strategy.name] = strategy

    def get(self, name: str) -> Strategy | None:
        return self._strategies.get(name)

    def get_all(self) -> list[Strategy]:
        return list(self._strategies.values())

    def get_enabled(self) -> list[Strategy]:
        # TODO: Check database for enabled strategies
        return self.get_all()
```

### 3.2 Signal Generator

```python
# src/polybot/trading/signals.py
import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.signal import Signal
from ..models.market import Market
from ..services.llm.analyzer import LLMAnalyzer
from ..services.qdrant.client import QdrantService
from ..services.polymarket.client import PolymarketClient
from ..config import get_settings

class SignalGenerator:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.settings = get_settings()
        self.llm = LLMAnalyzer()
        self.qdrant = QdrantService()
        self.polymarket = PolymarketClient()

    async def process_message(
        self,
        text: str,
        source: str,
    ) -> list[Signal]:
        """Process a message and generate signals."""

        # 1. Find relevant markets
        markets = await self._find_markets(text)
        if not markets:
            return []

        # 2. Analyze each market with LLM
        signals = []
        for market in markets[:10]:  # Limit to top 10
            analysis = await self.llm.analyze_market(
                message_text=text,
                market_question=market.question,
                market_description=market.description,
            )

            if not analysis.is_relevant:
                continue
            if analysis.confidence < self.settings.min_confidence:
                continue

            # 3. Get price and check spread
            token_idx = 0 if analysis.side == "Yes" else 1
            token_id = market.clob_token_ids[token_idx]

            bid, ask = await self.polymarket.get_best_price(token_id)
            spread = ((ask - bid) / ask) * 100 if ask > 0 else 100

            if spread > self.settings.max_spread_percent:
                continue

            price = ask  # Entry at ask price
            if not (self.settings.min_entry_price <= price <= self.settings.max_entry_price):
                continue

            # 4. Create signal
            signal = Signal(
                id=str(uuid.uuid4()),
                market_id=market.condition_id,
                token_id=token_id,
                market_question=market.question,
                side=analysis.side,
                confidence=analysis.confidence,
                price_at_signal=price,
                source=source,
                message_text=text,
                keywords=[],
            )
            self.session.add(signal)
            signals.append(signal)

        await self.session.flush()
        return signals

    async def _find_markets(self, text: str) -> list[Market]:
        """Find relevant markets using RAG or keywords."""

        # Try semantic search first
        if self.qdrant.client:
            results = await self.qdrant.search(text, limit=10)
            if results:
                condition_ids = [r["condition_id"] for r in results]
                stmt = select(Market).where(
                    Market.condition_id.in_(condition_ids),
                    Market.active == True,
                )
                result = await self.session.execute(stmt)
                return list(result.scalars().all())

        # Fallback to keyword search
        keywords = await self.llm.extract_keywords(text)
        if not keywords:
            return []

        # Simple LIKE search
        stmt = select(Market).where(Market.active == True)
        result = await self.session.execute(stmt)
        markets = result.scalars().all()

        # Filter by keyword match (basic)
        matched = []
        for market in markets:
            text_lower = market.question.lower()
            if any(kw.lower() in text_lower for kw in keywords):
                matched.append(market)

        return matched[:10]
```

### 3.3 Position Manager

```python
# src/polybot/trading/positions.py
import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from ..models.position import Position, PositionStatus
from ..models.signal import Signal
from ..models.simulation import SimulationState
from .strategies.registry import StrategyRegistry
from .strategies.base import PositionContext, ExitDecision
from ..services.polymarket.client import PolymarketClient
from ..core.events import PositionOpened, PositionClosed, PriceUpdated
from ..core.bus import EventBus

class PositionManager:
    def __init__(
        self,
        session: AsyncSession,
        event_bus: EventBus,
        strategy_registry: StrategyRegistry,
    ):
        self.session = session
        self.event_bus = event_bus
        self.strategies = strategy_registry
        self.polymarket = PolymarketClient()

    async def open_from_signal(
        self,
        signal: Signal,
        strategy_name: str | None = None,
    ) -> list[Position]:
        """Open position(s) from a signal."""

        # Get simulation state
        state = await self._get_simulation_state()

        # Get strategies to use
        if strategy_name:
            strategies = [self.strategies.get(strategy_name)]
        else:
            strategies = self.strategies.get_enabled()

        positions = []
        for strategy in strategies:
            if not strategy:
                continue

            # Check if strategy wants this signal
            if not strategy.should_enter(
                confidence=signal.confidence,
                spread=0,  # Already checked in signal generation
                price=signal.price_at_signal,
            ):
                continue

            # Calculate size
            size_capital = strategy.calculate_size(
                state.available_capital / len(strategies),
                signal.confidence,
            )

            if size_capital <= 0:
                continue

            size = size_capital / signal.price_at_signal

            # Create position
            position = Position(
                id=str(uuid.uuid4()),
                signal_id=signal.id,
                market_id=signal.market_id,
                token_id=signal.token_id,
                market_question=signal.market_question,
                side=signal.side,
                strategy=strategy.name,
                entry_price=signal.price_at_signal,
                size=size,
                capital_allocated=size_capital,
                source=signal.source,
                current_price=signal.price_at_signal,
            )

            # Allocate capital
            state.available_capital -= size_capital
            state.allocated_capital += size_capital
            state.open_positions += 1

            self.session.add(position)
            positions.append(position)

            # Emit event
            await self.event_bus.publish(PositionOpened(
                position_id=position.id,
                signal_id=signal.id,
                strategy=strategy.name,
                entry_price=position.entry_price,
                size=size,
            ))

        await self.session.flush()
        return positions

    async def check_exits(self) -> list[Position]:
        """Check all open positions for exit conditions."""

        stmt = select(Position).where(Position.status == PositionStatus.OPEN)
        result = await self.session.execute(stmt)
        positions = list(result.scalars().all())

        closed = []
        for position in positions:
            # Fetch current price
            try:
                _, ask = await self.polymarket.get_best_price(position.token_id)
                current_price = ask
            except Exception:
                continue

            # Update current price
            position.current_price = current_price
            if position.peak_price is None or current_price > position.peak_price:
                position.peak_price = current_price

            # Build context
            hours_open = (datetime.utcnow() - position.created_at).total_seconds() / 3600
            ctx = PositionContext(
                position_id=position.id,
                entry_price=position.entry_price,
                current_price=current_price,
                size=position.size,
                capital_allocated=position.capital_allocated,
                side=position.side,
                peak_price=position.peak_price,
                opened_at=position.created_at,
                hours_open=hours_open,
            )

            # Check strategy
            strategy = self.strategies.get(position.strategy)
            if not strategy:
                continue

            decision = strategy.should_exit(ctx)

            if decision.should_exit:
                await self._close_position(position, current_price, decision)
                closed.append(position)
            else:
                # Update unrealized P&L
                position.unrealized_pnl = self._calc_pnl(position, current_price)

                await self.event_bus.publish(PriceUpdated(
                    position_id=position.id,
                    price=current_price,
                    pnl_percent=position.unrealized_pnl / position.capital_allocated,
                ))

        await self.session.flush()
        return closed

    async def _close_position(
        self,
        position: Position,
        exit_price: float,
        decision: ExitDecision,
    ):
        """Close a position."""

        position.status = PositionStatus.CLOSED
        position.exit_price = exit_price
        position.exit_reason = decision.reason
        position.closed_at = datetime.utcnow()
        position.pnl = self._calc_pnl(position, exit_price)

        # Update simulation state
        state = await self._get_simulation_state()
        state.available_capital += position.capital_allocated + position.pnl
        state.allocated_capital -= position.capital_allocated
        state.total_pnl += position.pnl
        state.open_positions -= 1
        state.closed_positions += 1

        await self.event_bus.publish(PositionClosed(
            position_id=position.id,
            exit_price=exit_price,
            pnl=position.pnl,
            reason=decision.reason,
        ))

    def _calc_pnl(self, position: Position, current_price: float) -> float:
        if position.side == "Yes":
            price_diff = current_price - position.entry_price
        else:
            price_diff = position.entry_price - current_price
        return price_diff * position.size

    async def _get_simulation_state(self) -> SimulationState:
        stmt = select(SimulationState).where(SimulationState.id == 1)
        result = await self.session.execute(stmt)
        state = result.scalar_one_or_none()
        if not state:
            state = SimulationState(id=1)
            self.session.add(state)
        return state
```

---

## Phase 4: Bot Orchestrator

### 4.1 Main Orchestrator

```python
# src/polybot/bot/orchestrator.py
import asyncio
from ..core.bus import EventBus
from ..core.events import MessageReceived, SignalCreated
from ..services.telegram.monitor import TelegramMonitor
from ..services.polymarket.harvester import MarketHarvester
from ..trading.signals import SignalGenerator
from ..trading.positions import PositionManager
from ..trading.strategies.registry import StrategyRegistry
from ..db.session import get_session
from ..config import get_settings

class TradingBot:
    def __init__(self):
        self.settings = get_settings()
        self.event_bus = EventBus()
        self.strategy_registry = StrategyRegistry()
        self._running = False

    async def start(self):
        """Start the trading bot."""
        self._running = True

        # Subscribe to events
        self.event_bus.subscribe(MessageReceived, self._on_message)

        # Start components
        self.telegram = TelegramMonitor(self.event_bus)
        await self.telegram.start()

        # Start background tasks
        asyncio.create_task(self._event_loop())
        asyncio.create_task(self._position_monitor_loop())
        asyncio.create_task(self._market_refresh_loop())

        print("Trading bot started")

    async def _event_loop(self):
        """Process events from the bus."""
        await self.event_bus.start()

    async def _on_message(self, event: MessageReceived):
        """Handle incoming Telegram message."""
        async with get_session() as session:
            generator = SignalGenerator(session)
            signals = await generator.process_message(
                text=event.text,
                source=f"telegram:{event.chat_title}",
            )

            if signals:
                manager = PositionManager(
                    session,
                    self.event_bus,
                    self.strategy_registry,
                )
                for signal in signals:
                    await manager.open_from_signal(signal)

    async def _position_monitor_loop(self):
        """Periodically check positions for exits."""
        while self._running:
            await asyncio.sleep(60)
            async with get_session() as session:
                manager = PositionManager(
                    session,
                    self.event_bus,
                    self.strategy_registry,
                )
                await manager.check_exits()

    async def _market_refresh_loop(self):
        """Periodically refresh market data."""
        while self._running:
            await asyncio.sleep(12 * 3600)  # 12 hours
            harvester = MarketHarvester()
            await harvester.harvest()

    async def stop(self):
        """Stop the trading bot."""
        self._running = False
        self.event_bus.stop()
        await self.telegram.stop()
        print("Trading bot stopped")
```

---

## Phase 5: API & UI

### 5.1 FastAPI Application

```python
# src/polybot/api/app.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
from .routes import dashboard, positions, signals, strategies, bot

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown

def create_app() -> FastAPI:
    app = FastAPI(
        title="Polymarket Trading Bot",
        lifespan=lifespan,
    )

    # Mount static files
    app.mount("/static", StaticFiles(directory="static"), name="static")

    # Include routers
    app.include_router(dashboard.router, prefix="/ui", tags=["UI"])
    app.include_router(positions.router, prefix="/api/positions", tags=["Positions"])
    app.include_router(signals.router, prefix="/api/signals", tags=["Signals"])
    app.include_router(strategies.router, prefix="/api/strategies", tags=["Strategies"])
    app.include_router(bot.router, prefix="/api/bot", tags=["Bot"])

    return app

app = create_app()
```

### 5.2 Dashboard Routes

```python
# src/polybot/api/routes/dashboard.py
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, func
from ...db.session import get_session
from ...models.position import Position, PositionStatus
from ...models.signal import Signal
from ...models.simulation import SimulationState

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    async with get_session() as session:
        # Get simulation state
        state = await session.scalar(
            select(SimulationState).where(SimulationState.id == 1)
        )

        # Get open positions
        positions = await session.scalars(
            select(Position)
            .where(Position.status == PositionStatus.OPEN)
            .order_by(Position.created_at.desc())
        )

        # Get recent signals
        signals = await session.scalars(
            select(Signal)
            .order_by(Signal.created_at.desc())
            .limit(10)
        )

        # Strategy stats
        strategy_stats = await session.execute(
            select(
                Position.strategy,
                func.count(Position.id).label("count"),
                func.sum(Position.pnl).label("total_pnl"),
            )
            .where(Position.status == PositionStatus.CLOSED)
            .group_by(Position.strategy)
        )

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "state": state,
            "positions": list(positions),
            "signals": list(signals),
            "strategy_stats": list(strategy_stats),
        },
    )
```

---

## Phase 6: Testing

### 6.1 Test Structure

```python
# tests/conftest.py
import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from polybot.models.base import Base
from polybot.config import Settings

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session

@pytest.fixture
def settings():
    return Settings(
        telegram_api_id=12345,
        telegram_api_hash="test",
        telegram_phone="+1234567890",
        openai_api_key="test",
    )
```

```python
# tests/unit/test_strategies.py
import pytest
from datetime import datetime, timedelta
from polybot.trading.strategies.builtin.general import GeneralStrategy
from polybot.trading.strategies.base import PositionContext

class TestGeneralStrategy:
    def test_should_enter_valid(self):
        strategy = GeneralStrategy()
        assert strategy.should_enter(
            confidence=0.8,
            spread=5.0,
            price=0.5,
        ) is True

    def test_should_enter_low_confidence(self):
        strategy = GeneralStrategy()
        assert strategy.should_enter(
            confidence=0.5,  # Below threshold
            spread=5.0,
            price=0.5,
        ) is False

    def test_take_profit_exit(self):
        strategy = GeneralStrategy()
        ctx = PositionContext(
            position_id="test",
            entry_price=0.5,
            current_price=0.8,  # 60% profit
            size=100,
            capital_allocated=50,
            side="Yes",
            peak_price=0.8,
            opened_at=datetime.utcnow(),
            hours_open=1.0,
        )
        decision = strategy.should_exit(ctx)
        assert decision.should_exit is True
        assert decision.reason == "take_profit"

    def test_stop_loss_exit(self):
        strategy = GeneralStrategy()
        ctx = PositionContext(
            position_id="test",
            entry_price=0.5,
            current_price=0.35,  # 30% loss
            size=100,
            capital_allocated=50,
            side="Yes",
            peak_price=0.5,
            opened_at=datetime.utcnow(),
            hours_open=1.0,
        )
        decision = strategy.should_exit(ctx)
        assert decision.should_exit is True
        assert decision.reason == "stop_loss"
```

---

## Implementation Order

### Week 1: Foundation
1. Project setup (pyproject.toml, directory structure)
2. Configuration system
3. Database models and migrations
4. Event system (events, bus)

### Week 2: External Services
1. Polymarket client (markets, orderbook)
2. Market harvester
3. Qdrant client (optional RAG)
4. LLM analyzer

### Week 3: Trading Core
1. Strategy base and registry
2. Built-in strategies (general, conservative, aggressive, trailing)
3. Signal generator
4. Position manager

### Week 4: Telegram & Bot
1. Telegram client and monitor
2. Bot orchestrator
3. Background tasks

### Week 5: API & UI
1. FastAPI application
2. Dashboard routes
3. HTMX templates
4. Position/Signal/Strategy endpoints

### Week 6: Polish
1. Testing (unit, integration)
2. Error handling and logging
3. Documentation
4. Docker setup

---

## Key Design Decisions

1. **Event-driven architecture** - Loose coupling between components
2. **Strategy as Protocol** - Easy to add custom strategies
3. **Async throughout** - Consistent async/await for all I/O
4. **SQLAlchemy 2.0** - Modern ORM with full async support
5. **Pydantic for config** - Type-safe configuration
6. **Single strategy per position** - Clean 1:1 mapping (user selects strategy)
7. **Repository pattern** - Database access abstraction
8. **Alembic migrations** - Proper schema versioning

---

## Files to Create First

1. `pyproject.toml` - Dependencies
2. `src/polybot/__init__.py` - Package
3. `src/polybot/config.py` - Settings
4. `src/polybot/core/events.py` - Events
5. `src/polybot/core/bus.py` - Event bus
6. `src/polybot/models/base.py` - SQLAlchemy base
7. `src/polybot/db/session.py` - Database session
