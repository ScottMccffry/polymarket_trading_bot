# Statistics & Analytics Design

## Overview

Comprehensive analytics suite for the Polymarket trading bot providing performance tracking, risk metrics, and trade analysis with real-time updates.

## Goals

- Visualize overall portfolio performance, PnL charts, win rates over time
- Compare how different strategies perform against each other
- Deep dive into individual trades, identify patterns in winners/losers
- Track drawdowns, Sharpe ratio, risk-adjusted returns
- Maximum flexibility to interpret data and increase performance

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js)                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ Dashboard   │  │ Filter Bar  │  │ Charts (Lightweight)    │  │
│  │ Overview    │  │ (ShadCN)    │  │ + Tables (ShadCN)       │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
│                           │                                      │
│                    WebSocket Connection                          │
└───────────────────────────┼─────────────────────────────────────┘
                            │
┌───────────────────────────┼─────────────────────────────────────┐
│                     Backend (FastAPI)                            │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              Analytics Service                           │    │
│  │  - Metrics calculator (PnL, Sharpe, drawdown, etc.)     │    │
│  │  - Flexible grouping/filtering engine                    │    │
│  │  - Time aggregation (trade → daily → weekly → monthly)  │    │
│  └─────────────────────────────────────────────────────────┘    │
│                            │                                     │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              WebSocket Manager                           │    │
│  │  - Broadcasts stats on position changes                  │    │
│  │  - Client subscription management                        │    │
│  └─────────────────────────────────────────────────────────┘    │
│                            │                                     │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              Existing: Positions Table                   │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

**Key decisions:**
- Computed on-demand (no pre-aggregation tables)
- Real-time WebSocket updates
- No new database tables - analytics computed from existing `positions` table

## API Endpoints

### GET /api/analytics/summary

Returns overall metrics with optional grouping.

**Parameters:**
- `group_by` - any combination of position fields (strategy_name, source, trading_mode, side)
- `start_date`, `end_date` - date range filter
- `trading_mode` - live, paper, or all
- `status` - open, closed, or all

### GET /api/analytics/timeseries

Returns time-bucketed data for charts.

**Parameters:**
- `granularity` - daily, weekly, monthly
- `metric` - pnl, equity, drawdown, win_rate
- `group_by` - optional segmentation
- `start_date`, `end_date` - date range

### GET /api/analytics/trades

Returns paginated trade list with full details.

**Parameters:**
- `sort_by` - realized_pnl, opened_at, size
- `order` - asc, desc
- `limit`, `offset` - pagination
- `filters[field]` - any position field

### GET /api/analytics/heatmap

Returns heatmap data for time-based pattern analysis.

**Parameters:**
- `dimension` - day_of_week, hour_of_day, month
- `metric` - pnl, win_rate, trade_count

### WebSocket /ws/analytics

Real-time stats updates.

**Subscribe:** `{ "filters": {...}, "group_by": [...] }`
**Receives:** `{ "type": "stats_update", "data": {...} }`

## Metrics Calculated

### Basic PnL Metrics
- Total realized PnL ($ and %)
- Total unrealized PnL ($ and %)
- Average win / Average loss
- Win rate (% of profitable trades)
- Total trades / Open trades / Closed trades

### Risk-Adjusted Metrics
- Sharpe ratio
- Sortino ratio
- Max drawdown ($ and %)
- Current drawdown
- Risk/reward ratio
- Calmar ratio

### Trading Efficiency
- Profit factor (gross profit / gross loss)
- Expectancy (avg $ per trade)
- Average hold time
- Trade frequency
- Best trade / Worst trade
- Longest winning streak / Losing streak

### Time Series Data
- Cumulative equity curve
- Drawdown curve
- Rolling Sharpe (30-day window)
- Rolling win rate

### Heatmap Data
- PnL by day of week
- PnL by hour of day
- Win rate by day/hour
- Trade count distribution

## Frontend Dashboard

### Layout

```
┌────────────────────────────────────────────────────────────────────┐
│  FILTER BAR (sticky top)                                           │
│  [Date Range] [Strategy] [Source] [Mode] [Status]    [Apply]       │
└────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────┐
│  MODE TOGGLE                                 [LIVE] [Paper] [All]  │
└────────────────────────────────────────────────────────────────────┘

┌─────────────────────┬─────────────────────┬─────────────────────────┐
│   TOTAL PNL         │   WIN RATE          │   SHARPE RATIO          │
├─────────────────────┴─────────────────────┴─────────────────────────┤
│   MAX DRAWDOWN      │   PROFIT FACTOR     │   OPEN POSITIONS        │
└─────────────────────┴─────────────────────┴─────────────────────────┘

┌────────────────────────────────────────────────────────────────────┐
│  EQUITY CURVE (Lightweight Charts)                    [1W 1M 3M ALL]│
└────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────┬─────────────────────────────────────┐
│  DRAWDOWN CHART              │  PERFORMANCE HEATMAP                │
└──────────────────────────────┴─────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────┐
│  STRATEGY COMPARISON TABLE                                         │
└────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────┐
│  RECENT TRADES TABLE                                               │
└────────────────────────────────────────────────────────────────────┘
```

### Live vs Paper Handling

- Dashboard defaults to `trading_mode=live`
- Three-way toggle: Live (default) / Paper / All
- Clear "LIVE" indicator when viewing live data
- Paper trades shown with muted styling when viewing "All"

## Backend File Structure

```
backend/app/
├── services/
│   └── analytics/
│       ├── __init__.py
│       ├── calculator.py      # Core metrics calculations
│       ├── aggregator.py      # Time bucketing
│       ├── filters.py         # Dynamic filtering & grouping
│       └── websocket.py       # Real-time broadcast manager
├── routes/
│   └── analytics.py           # REST endpoints
└── models/
    └── analytics.py           # Pydantic response schemas
```

## Frontend File Structure

```
frontend/src/
├── app/
│   └── analytics/
│       └── page.tsx
├── components/
│   └── analytics/
│       ├── FilterBar.tsx
│       ├── ModeToggle.tsx
│       ├── KpiCards.tsx
│       ├── EquityCurve.tsx
│       ├── DrawdownChart.tsx
│       ├── PerformanceHeatmap.tsx
│       ├── StrategyTable.tsx
│       └── TradesTable.tsx
├── hooks/
│   └── useAnalytics.ts
├── lib/
│   └── analytics-api.ts
└── types/
    └── analytics.ts
```

## Error Handling

### Empty States
- No positions → "No trades to analyze"
- No matching filters → "No trades match your filters" + clear button
- No live trades → Prompt to switch to Paper view

### Data Edge Cases
- Division by zero → Display "N/A"
- Single trade → Skip multi-trade metrics
- All losses → Win rate 0%, calculate others normally
- Open positions → Exclude from realized, include in unrealized

### WebSocket Resilience
- Connection lost → "Reconnecting..." with auto-retry
- Reconnected → Re-fetch full state
- Stale data warning after 30s disconnect

### Performance
- Trade table limited to 100 rows default
- Debounce filter changes (300ms)
- Loading skeletons during fetch

### API Errors
- 400 → Show validation error
- 500 → "Unable to load" + auto-retry
- Timeout → Same as 500
