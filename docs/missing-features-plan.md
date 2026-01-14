# Missing Features Plan

## Overview
Comparison between OLD version (`~/poly_tb/poly_trading_bot/`) and NEW version (`~/polymarket_trading_bot/`) showing features that still need to be ported.

---

## Completed (Ported)

| Feature | Status | Location |
|---------|--------|----------|
| Trading Strategies | Done | `backend/app/services/trading/strategies/` |
| Strategy Executor | Done | `backend/app/services/trading/executor.py` |
| Simulation Engine | Done | `backend/app/services/trading/simulation.py` |
| Position Check Scheduler | Done | `backend/app/services/scheduler/jobs.py` |
| Market Price History | Done | `backend/app/routes/markets.py` |

---

## Missing Features (To Be Ported)

### 1. Bot Orchestrator
**Priority: HIGH**

The main trading bot loop that monitors signals and executes trades.

**OLD Location:** `src/bot/orchestrator.py`

**What it does:**
- Monitors Telegram for new messages
- Processes messages through LLM for signal extraction
- Opens positions based on signals
- Runs position exit checks
- Refreshes markets periodically

**To implement:**
```
backend/app/services/bot/
├── __init__.py
├── orchestrator.py      # Main bot class
├── signal_processor.py  # Process signals from sources
└── position_manager.py  # Open/close positions
```

---

### 2. Statistics & Analytics
**Priority: HIGH**

Performance tracking and analytics module.

**OLD Location:** `src/statistics/`
- `analyzer.py` - Main statistics analyzer
- `performance_tracker.py` - Track P&L, win rate, etc.
- `source_analytics.py` - Per-source performance
- `impact_tracker.py` - Market impact analysis

**Metrics to track:**
- Win rate (overall and per source)
- Profit factor
- Sharpe ratio
- Max drawdown
- Average hold time
- Best/worst trades

**To implement:**
```
backend/app/services/statistics/
├── __init__.py
├── analyzer.py
├── performance.py
└── source_analytics.py
```

**API Routes needed:**
```
GET /api/statistics/overview
GET /api/statistics/performance
GET /api/statistics/by-source
GET /api/statistics/by-strategy
GET /api/statistics/daily
GET /api/statistics/trades
```

---

### 3. WebSocket Real-time Updates
**Priority: MEDIUM**

Push real-time updates to frontend.

**OLD Location:** `src/api/websocket.py`

**What it does:**
- Pushes position updates
- Pushes new signals
- Pushes P&L changes
- Dashboard auto-refresh

**To implement:**
```
backend/app/services/websocket/
├── __init__.py
├── manager.py           # Connection manager
└── events.py            # Event types
```

---

### 4. Bot Control API
**Priority: MEDIUM**

Start/stop/status endpoints for the trading bot.

**OLD Location:** `src/api/routes/bot.py`

**Endpoints needed:**
```
POST /api/bot/start
POST /api/bot/stop
GET  /api/bot/status
POST /api/bot/config
```

---

### 5. LLM Signal Analysis
**Priority: MEDIUM**

Use LLM to extract trading signals from messages.

**OLD Location:** `src/services/llm/`
- `analysis.py` - Analyze messages for signals
- `keywords.py` - Extract keywords

**To implement:**
```
backend/app/services/llm/
├── __init__.py
├── client.py            # OpenAI client wrapper
├── analysis.py          # Signal extraction
└── prompts.py           # Prompt templates
```

---

### 6. Message Processing Log
**Priority: LOW**

Track processed messages and their outcomes.

**What it does:**
- Log all processed messages
- Track which became signals
- Track which were ignored
- Debug signal generation

**To implement:**
- Add `message_log` table
- Add `/api/messages` routes

---

### 7. Frontend Statistics Page
**Priority: MEDIUM**

The `/statistics` page needs actual data.

**Current state:** Page exists but shows placeholder data

**Needs:**
- Connect to statistics API
- Charts for P&L over time
- Win rate by source
- Strategy performance comparison
- Trade history table

---

### 8. Position Opening Logic
**Priority: HIGH**

Logic to open new positions from signals.

**What it does:**
- Receive signal
- Find matching market
- Calculate position size
- Execute simulated trade
- Store position

**To implement in:** `backend/app/services/trading/executor.py`

```python
async def open_position(
    self,
    db: AsyncSession,
    signal: Signal,
    strategy_id: int,
) -> Position:
    # 1. Get market data
    # 2. Calculate position size
    # 3. Check available capital
    # 4. Create position record
    # 5. Update simulation state
```

---

## Implementation Priority Order

### Phase 1: Core Trading (Week 1)
1. Position Opening Logic
2. Bot Orchestrator (basic version)
3. LLM Signal Analysis

### Phase 2: Analytics (Week 2)
4. Statistics Module
5. Frontend Statistics Page
6. Message Processing Log

### Phase 3: Real-time (Week 3)
7. WebSocket Updates
8. Bot Control API
9. Dashboard improvements

---

## Database Tables Needed

```sql
-- Message log for debugging
CREATE TABLE message_log (
    id INTEGER PRIMARY KEY,
    source VARCHAR(100),
    message_text TEXT,
    processed_at TIMESTAMP,
    became_signal BOOLEAN,
    signal_id VARCHAR(255),
    error_message TEXT
);

-- Daily statistics cache
CREATE TABLE daily_stats (
    date DATE PRIMARY KEY,
    total_pnl FLOAT,
    trades_opened INTEGER,
    trades_closed INTEGER,
    win_count INTEGER,
    loss_count INTEGER,
    volume FLOAT
);
```

---

## API Routes Summary

### Currently Missing
| Route | Method | Description |
|-------|--------|-------------|
| `/api/bot/start` | POST | Start trading bot |
| `/api/bot/stop` | POST | Stop trading bot |
| `/api/bot/status` | GET | Bot running status |
| `/api/statistics/overview` | GET | Overall performance |
| `/api/statistics/by-source` | GET | Per-source stats |
| `/api/statistics/by-strategy` | GET | Per-strategy stats |
| `/api/messages` | GET | Processed messages log |
| `/api/ws` | WS | WebSocket connection |

---

## Notes

- The NEW version has better architecture (async, React frontend)
- The OLD version has complete trading logic
- Strategy execution is now working (just ported)
- Main gap is the orchestrator that ties everything together
