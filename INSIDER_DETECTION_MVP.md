# Polymarket Insider Detection System - MVP Specification

## Executive Summary

A real-time system that detects potential insider trading on Polymarket by monitoring on-chain activity, scoring wallets for suspicious behavior, and optionally copy-trading high-confidence insider positions.

**Core Value Proposition**: Turn Polymarket's transparency against insiders - their trades are public, their patterns are detectable, and their alpha can be captured.

---

## MVP Scope

### In Scope (MVP)
- Real-time trade monitoring via Polygon RPC/subgraphs
- Wallet profiling and scoring
- Insider detection alerts
- Manual copy-trade execution
- Web dashboard for monitoring
- Historical analysis

### Out of Scope (Post-MVP)
- Automated copy-trading execution
- Multi-chain support
- Mobile app
- Social features (leaderboards)
- ML-based pattern detection
- Backtest engine

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         DATA INGESTION LAYER                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │  Polygon RPC │  │   Goldsky    │  │  Polymarket  │              │
│  │   WebSocket  │  │   GraphQL    │  │  Gamma API   │              │
│  │              │  │              │  │              │              │
│  │ OrderFilled  │  │  Positions   │  │   Markets    │              │
│  │   Events     │  │   History    │  │   Metadata   │              │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘              │
│         │                 │                 │                       │
│         └────────────┬────┴─────────────────┘                       │
│                      ▼                                              │
│              ┌───────────────┐                                      │
│              │  Event Queue  │  (Redis Streams)                     │
│              └───────┬───────┘                                      │
│                      │                                              │
└──────────────────────┼──────────────────────────────────────────────┘
                       │
┌──────────────────────┼──────────────────────────────────────────────┐
│                      ▼         PROCESSING LAYER                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                     Trade Processor                           │  │
│  │                                                               │  │
│  │  1. Parse OrderFilled event                                   │  │
│  │  2. Enrich with market metadata                               │  │
│  │  3. Lookup/create wallet profile                              │  │
│  │  4. Update wallet statistics                                  │  │
│  │  5. Run detection algorithms                                  │  │
│  │  6. Calculate insider score                                   │  │
│  │  7. Emit alerts if threshold exceeded                         │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐     │
│  │  Wallet Scorer  │  │ Pattern Matcher │  │  Alert Engine   │     │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘     │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                       │
┌──────────────────────┼──────────────────────────────────────────────┐
│                      ▼         STORAGE LAYER                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │  PostgreSQL  │  │    Redis     │  │  TimescaleDB │              │
│  │              │  │              │  │  (optional)  │              │
│  │  - Wallets   │  │  - Cache     │  │              │              │
│  │  - Trades    │  │  - Sessions  │  │  - Price     │              │
│  │  - Alerts    │  │  - Queues    │  │    History   │              │
│  │  - Markets   │  │  - Pub/Sub   │  │  - Analytics │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                       │
┌──────────────────────┼──────────────────────────────────────────────┐
│                      ▼         PRESENTATION LAYER                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │   REST API   │  │  WebSocket   │  │  Dashboard   │              │
│  │              │  │    Server    │  │    (HTMX)    │              │
│  │  /wallets    │  │              │  │              │              │
│  │  /trades     │  │  Real-time   │  │  Live feed   │              │
│  │  /alerts     │  │  alerts      │  │  Wallet view │              │
│  │  /markets    │  │  trade feed  │  │  Analytics   │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    Telegram Bot (Alerts)                      │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Database Schema

### Core Tables

```sql
-- Wallet profiles with insider scoring
CREATE TABLE wallets (
    address TEXT PRIMARY KEY,
    proxy_address TEXT,                    -- Polymarket proxy wallet

    -- Account metadata
    first_seen_at TIMESTAMPTZ NOT NULL,
    first_trade_at TIMESTAMPTZ,
    last_trade_at TIMESTAMPTZ,

    -- Trading statistics
    total_trades INTEGER DEFAULT 0,
    total_volume_usd DECIMAL(18,2) DEFAULT 0,
    total_markets_traded INTEGER DEFAULT 0,

    -- Performance metrics
    realized_pnl DECIMAL(18,2) DEFAULT 0,
    win_count INTEGER DEFAULT 0,
    loss_count INTEGER DEFAULT 0,

    -- Insider scoring
    insider_score DECIMAL(5,2) DEFAULT 0,  -- 0-100
    last_score_update TIMESTAMPTZ,

    -- Flags
    is_watched BOOLEAN DEFAULT FALSE,
    is_blocked BOOLEAN DEFAULT FALSE,      -- Known market maker, etc.
    tags TEXT[],                           -- ['new_account', 'high_volume', etc.]

    -- Metadata
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for fast lookups
CREATE INDEX idx_wallets_insider_score ON wallets(insider_score DESC);
CREATE INDEX idx_wallets_first_trade ON wallets(first_trade_at);
CREATE INDEX idx_wallets_watched ON wallets(is_watched) WHERE is_watched = TRUE;


-- Individual trades
CREATE TABLE trades (
    id BIGSERIAL PRIMARY KEY,
    tx_hash TEXT NOT NULL,
    log_index INTEGER NOT NULL,

    -- Participants
    wallet_address TEXT NOT NULL REFERENCES wallets(address),

    -- Market info
    market_id TEXT NOT NULL,
    token_id TEXT NOT NULL,
    outcome TEXT NOT NULL,                 -- 'Yes' or 'No'

    -- Trade details
    side TEXT NOT NULL,                    -- 'buy' or 'sell'
    price DECIMAL(10,6) NOT NULL,
    size DECIMAL(18,6) NOT NULL,
    volume_usd DECIMAL(18,2) NOT NULL,

    -- Market context at trade time
    market_odds_before DECIMAL(10,6),
    market_odds_after DECIMAL(10,6),
    market_volume_24h DECIMAL(18,2),

    -- Slippage analysis
    mid_price_at_trade DECIMAL(10,6),
    slippage_percent DECIMAL(8,4),

    -- Timing
    block_number BIGINT NOT NULL,
    block_timestamp TIMESTAMPTZ NOT NULL,

    -- Detection flags
    flags TEXT[],                          -- ['large_trade', 'new_wallet', etc.]

    UNIQUE(tx_hash, log_index)
);

-- Indexes for analysis
CREATE INDEX idx_trades_wallet ON trades(wallet_address);
CREATE INDEX idx_trades_market ON trades(market_id);
CREATE INDEX idx_trades_timestamp ON trades(block_timestamp DESC);
CREATE INDEX idx_trades_volume ON trades(volume_usd DESC);


-- Markets cache
CREATE TABLE markets (
    condition_id TEXT PRIMARY KEY,
    question TEXT NOT NULL,
    description TEXT,
    category TEXT,

    -- Tokens
    yes_token_id TEXT,
    no_token_id TEXT,

    -- Status
    end_date TIMESTAMPTZ,
    resolved BOOLEAN DEFAULT FALSE,
    resolution_outcome TEXT,               -- 'Yes', 'No', or NULL
    resolution_time TIMESTAMPTZ,

    -- Metrics
    volume_total DECIMAL(18,2) DEFAULT 0,
    liquidity DECIMAL(18,2) DEFAULT 0,

    -- Tracking
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);


-- Insider alerts
CREATE TABLE alerts (
    id BIGSERIAL PRIMARY KEY,

    -- Alert details
    alert_type TEXT NOT NULL,              -- 'new_wallet_large_bet', 'high_win_rate', etc.
    severity TEXT NOT NULL,                -- 'low', 'medium', 'high', 'critical'

    -- Context
    wallet_address TEXT REFERENCES wallets(address),
    trade_id BIGINT REFERENCES trades(id),
    market_id TEXT REFERENCES markets(condition_id),

    -- Scoring
    confidence_score DECIMAL(5,2),         -- 0-100

    -- Alert content
    title TEXT NOT NULL,
    description TEXT,
    metadata JSONB,                        -- Flexible additional data

    -- Status
    status TEXT DEFAULT 'new',             -- 'new', 'viewed', 'actioned', 'dismissed'
    actioned_at TIMESTAMPTZ,
    action_taken TEXT,                     -- 'copied', 'ignored', etc.

    -- Outcome tracking
    outcome_tracked BOOLEAN DEFAULT FALSE,
    outcome_pnl DECIMAL(18,2),

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_alerts_status ON alerts(status, created_at DESC);
CREATE INDEX idx_alerts_severity ON alerts(severity, created_at DESC);
CREATE INDEX idx_alerts_wallet ON alerts(wallet_address);


-- Wallet market concentration
CREATE TABLE wallet_market_stats (
    wallet_address TEXT REFERENCES wallets(address),
    market_id TEXT REFERENCES markets(condition_id),

    -- Position
    side TEXT,                             -- 'Yes' or 'No'
    total_bought DECIMAL(18,6) DEFAULT 0,
    total_sold DECIMAL(18,6) DEFAULT 0,
    net_position DECIMAL(18,6) DEFAULT 0,
    avg_entry_price DECIMAL(10,6),

    -- Volume
    total_volume_usd DECIMAL(18,2) DEFAULT 0,
    trade_count INTEGER DEFAULT 0,

    -- Timing
    first_trade_at TIMESTAMPTZ,
    last_trade_at TIMESTAMPTZ,

    -- Outcome (after resolution)
    pnl DECIMAL(18,2),
    won BOOLEAN,

    PRIMARY KEY (wallet_address, market_id)
);


-- Win rate tracking by category
CREATE TABLE wallet_category_stats (
    wallet_address TEXT REFERENCES wallets(address),
    category TEXT NOT NULL,                -- 'politics', 'crypto', 'sports', etc.

    total_trades INTEGER DEFAULT 0,
    total_volume_usd DECIMAL(18,2) DEFAULT 0,
    win_count INTEGER DEFAULT 0,
    loss_count INTEGER DEFAULT 0,
    total_pnl DECIMAL(18,2) DEFAULT 0,

    -- Derived
    win_rate DECIMAL(5,4),                 -- 0.0000 to 1.0000

    PRIMARY KEY (wallet_address, category)
);


-- Watchlist for manual tracking
CREATE TABLE watchlist (
    id BIGSERIAL PRIMARY KEY,
    wallet_address TEXT REFERENCES wallets(address),

    reason TEXT,
    added_by TEXT,                         -- User who added

    -- Notifications
    notify_on_trade BOOLEAN DEFAULT TRUE,
    notify_threshold_usd DECIMAL(18,2),    -- Min trade size to notify

    created_at TIMESTAMPTZ DEFAULT NOW()
);


-- Copy trade tracking
CREATE TABLE copy_trades (
    id BIGSERIAL PRIMARY KEY,

    -- Source
    alert_id BIGINT REFERENCES alerts(id),
    source_wallet TEXT REFERENCES wallets(address),
    source_trade_id BIGINT REFERENCES trades(id),

    -- Our trade
    our_trade_tx TEXT,
    our_entry_price DECIMAL(10,6),
    our_size DECIMAL(18,6),
    our_volume_usd DECIMAL(18,2),

    -- Status
    status TEXT DEFAULT 'open',            -- 'open', 'closed', 'cancelled'
    exit_price DECIMAL(10,6),
    exit_tx TEXT,

    -- P&L
    pnl DECIMAL(18,2),
    pnl_percent DECIMAL(8,4),

    created_at TIMESTAMPTZ DEFAULT NOW(),
    closed_at TIMESTAMPTZ
);
```

---

## Detection Algorithms

### Algorithm 1: New Wallet Large Bet (NWLB)

**Trigger**: Every new trade

```python
def detect_new_wallet_large_bet(trade: Trade, wallet: Wallet) -> Alert | None:
    """
    Detect new wallets placing unusually large bets.

    Based on: Venezuela case ($32k bet, 1-week-old account)
              OpenAI Browser case ($40k bet, brand new wallet)
    """

    # Thresholds
    MAX_ACCOUNT_AGE_DAYS = 7
    LARGE_BET_THRESHOLD_USD = 10_000
    CRITICAL_BET_THRESHOLD_USD = 40_000

    account_age_days = (now() - wallet.first_trade_at).days

    if account_age_days > MAX_ACCOUNT_AGE_DAYS:
        return None

    if trade.volume_usd < LARGE_BET_THRESHOLD_USD:
        return None

    # Calculate severity
    if account_age_days <= 1 and trade.volume_usd >= CRITICAL_BET_THRESHOLD_USD:
        severity = "critical"
        confidence = 90
    elif account_age_days <= 3 and trade.volume_usd >= LARGE_BET_THRESHOLD_USD:
        severity = "high"
        confidence = 75
    else:
        severity = "medium"
        confidence = 60

    return Alert(
        alert_type="new_wallet_large_bet",
        severity=severity,
        confidence_score=confidence,
        title=f"New wallet ({account_age_days}d) placed ${trade.volume_usd:,.0f} bet",
        metadata={
            "account_age_days": account_age_days,
            "trade_volume_usd": trade.volume_usd,
            "market_question": trade.market.question,
            "side": trade.outcome,
        }
    )
```

### Algorithm 2: Single Market Concentration (SMC)

**Trigger**: After updating wallet stats

```python
def detect_single_market_concentration(wallet: Wallet) -> Alert | None:
    """
    Detect wallets with all/most activity in a single market.

    Based on: Nobel Prize case (single market focus)
              Venezuela case (only Maduro-related bets)
    """

    # Thresholds
    MIN_VOLUME_USD = 5_000
    CONCENTRATION_THRESHOLD = 0.90  # 90% in one market

    if wallet.total_volume_usd < MIN_VOLUME_USD:
        return None

    # Get market breakdown
    market_stats = get_wallet_market_stats(wallet.address)

    if not market_stats:
        return None

    # Calculate concentration
    top_market = max(market_stats, key=lambda x: x.total_volume_usd)
    concentration = top_market.total_volume_usd / wallet.total_volume_usd

    if concentration < CONCENTRATION_THRESHOLD:
        return None

    # Higher severity for newer accounts
    account_age_days = (now() - wallet.first_trade_at).days

    if account_age_days <= 7 and concentration >= 0.95:
        severity = "high"
        confidence = 80
    elif concentration >= 0.95:
        severity = "medium"
        confidence = 65
    else:
        severity = "low"
        confidence = 50

    return Alert(
        alert_type="single_market_concentration",
        severity=severity,
        confidence_score=confidence,
        title=f"Wallet has {concentration:.0%} volume in single market",
        metadata={
            "concentration": concentration,
            "market_id": top_market.market_id,
            "market_volume_usd": top_market.total_volume_usd,
            "total_volume_usd": wallet.total_volume_usd,
        }
    )
```

### Algorithm 3: Abnormal Win Rate (AWR)

**Trigger**: After market resolution

```python
def detect_abnormal_win_rate(wallet: Wallet, category: str = None) -> Alert | None:
    """
    Detect wallets with suspiciously high win rates.

    Based on: Google Year in Search (96% win rate, 22/23)
              AlphaRaccoon pattern
    """

    # Thresholds
    MIN_RESOLVED_TRADES = 5
    HIGH_WIN_RATE = 0.75
    CRITICAL_WIN_RATE = 0.90

    if category:
        stats = get_wallet_category_stats(wallet.address, category)
    else:
        stats = wallet

    total_resolved = stats.win_count + stats.loss_count

    if total_resolved < MIN_RESOLVED_TRADES:
        return None

    win_rate = stats.win_count / total_resolved

    if win_rate < HIGH_WIN_RATE:
        return None

    # Calculate severity
    if win_rate >= CRITICAL_WIN_RATE and total_resolved >= 10:
        severity = "critical"
        confidence = 95
    elif win_rate >= CRITICAL_WIN_RATE:
        severity = "high"
        confidence = 85
    elif win_rate >= HIGH_WIN_RATE and total_resolved >= 10:
        severity = "medium"
        confidence = 70
    else:
        severity = "low"
        confidence = 55

    return Alert(
        alert_type="abnormal_win_rate",
        severity=severity,
        confidence_score=confidence,
        title=f"Wallet has {win_rate:.0%} win rate ({stats.win_count}/{total_resolved})",
        metadata={
            "win_rate": win_rate,
            "wins": stats.win_count,
            "losses": stats.loss_count,
            "category": category,
            "total_pnl": stats.total_pnl,
        }
    )
```

### Algorithm 4: High Slippage Tolerance (HST)

**Trigger**: Every trade

```python
def detect_high_slippage_tolerance(trade: Trade, wallet: Wallet) -> Alert | None:
    """
    Detect traders willing to pay above-market prices.

    Rationale: Insiders don't care about 5% slippage if they expect 50%+ returns.
    """

    # Thresholds
    MIN_VOLUME_USD = 5_000
    HIGH_SLIPPAGE_PERCENT = 3.0
    CRITICAL_SLIPPAGE_PERCENT = 5.0

    if trade.volume_usd < MIN_VOLUME_USD:
        return None

    if trade.slippage_percent is None or trade.slippage_percent < HIGH_SLIPPAGE_PERCENT:
        return None

    # More significant if account is new
    account_age_days = (now() - wallet.first_trade_at).days

    if trade.slippage_percent >= CRITICAL_SLIPPAGE_PERCENT and account_age_days <= 7:
        severity = "high"
        confidence = 75
    elif trade.slippage_percent >= CRITICAL_SLIPPAGE_PERCENT:
        severity = "medium"
        confidence = 60
    else:
        severity = "low"
        confidence = 45

    return Alert(
        alert_type="high_slippage_tolerance",
        severity=severity,
        confidence_score=confidence,
        title=f"Trader paid {trade.slippage_percent:.1f}% above mid on ${trade.volume_usd:,.0f}",
        metadata={
            "slippage_percent": trade.slippage_percent,
            "mid_price": trade.mid_price_at_trade,
            "trade_price": trade.price,
            "volume_usd": trade.volume_usd,
        }
    )
```

### Algorithm 5: Market Impact (MI)

**Trigger**: Every trade

```python
def detect_market_impact(trade: Trade) -> Alert | None:
    """
    Detect single trades that significantly move market odds.

    Based on: Taylor Swift case (12% odds movement)
              Nobel Prize case (68% odds movement over hours)
    """

    # Thresholds
    MIN_IMPACT_PERCENT = 5.0
    HIGH_IMPACT_PERCENT = 10.0
    CRITICAL_IMPACT_PERCENT = 20.0

    if trade.market_odds_before is None or trade.market_odds_after is None:
        return None

    impact = abs(trade.market_odds_after - trade.market_odds_before) * 100

    if impact < MIN_IMPACT_PERCENT:
        return None

    if impact >= CRITICAL_IMPACT_PERCENT:
        severity = "critical"
        confidence = 85
    elif impact >= HIGH_IMPACT_PERCENT:
        severity = "high"
        confidence = 70
    else:
        severity = "medium"
        confidence = 55

    return Alert(
        alert_type="market_impact",
        severity=severity,
        confidence_score=confidence,
        title=f"Trade moved market by {impact:.1f}%",
        metadata={
            "odds_before": trade.market_odds_before,
            "odds_after": trade.market_odds_after,
            "impact_percent": impact,
            "volume_usd": trade.volume_usd,
        }
    )
```

### Algorithm 6: Coordinated Wallets (CW)

**Trigger**: Periodic scan (every hour)

```python
def detect_coordinated_wallets(market_id: str) -> Alert | None:
    """
    Detect multiple new wallets betting same direction.

    Based on: French trader Théo (11 coordinated wallets)
              Nobel Prize (3 accounts, same direction)
    """

    # Get recent trades in market
    recent_trades = get_market_trades(
        market_id=market_id,
        since=now() - timedelta(hours=24)
    )

    # Filter to new wallets (< 30 days)
    new_wallet_trades = [
        t for t in recent_trades
        if (now() - t.wallet.first_trade_at).days < 30
    ]

    if len(new_wallet_trades) < 3:
        return None

    # Group by direction
    yes_wallets = set(t.wallet_address for t in new_wallet_trades if t.outcome == "Yes")
    no_wallets = set(t.wallet_address for t in new_wallet_trades if t.outcome == "No")

    # Check for coordination
    max_same_direction = max(len(yes_wallets), len(no_wallets))
    direction = "Yes" if len(yes_wallets) > len(no_wallets) else "No"

    if max_same_direction < 3:
        return None

    # Calculate total volume
    same_direction_trades = [
        t for t in new_wallet_trades if t.outcome == direction
    ]
    total_volume = sum(t.volume_usd for t in same_direction_trades)

    if max_same_direction >= 5 and total_volume >= 50_000:
        severity = "critical"
        confidence = 85
    elif max_same_direction >= 3 and total_volume >= 20_000:
        severity = "high"
        confidence = 70
    else:
        severity = "medium"
        confidence = 55

    return Alert(
        alert_type="coordinated_wallets",
        severity=severity,
        confidence_score=confidence,
        title=f"{max_same_direction} new wallets betting {direction} (${total_volume:,.0f})",
        metadata={
            "wallet_count": max_same_direction,
            "direction": direction,
            "total_volume_usd": total_volume,
            "wallet_addresses": list(yes_wallets if direction == "Yes" else no_wallets),
        }
    )
```

### Composite Insider Score

```python
def calculate_insider_score(wallet: Wallet, recent_alerts: list[Alert]) -> float:
    """
    Calculate overall insider probability score (0-100).

    Combines multiple signals with weights.
    """

    score = 0.0

    # Base score from account characteristics
    account_age_days = (now() - wallet.first_trade_at).days

    if account_age_days <= 1:
        score += 20
    elif account_age_days <= 7:
        score += 15
    elif account_age_days <= 30:
        score += 5

    # Score from alerts
    alert_weights = {
        "new_wallet_large_bet": 25,
        "single_market_concentration": 20,
        "abnormal_win_rate": 30,
        "high_slippage_tolerance": 15,
        "market_impact": 15,
        "coordinated_wallets": 25,
    }

    for alert in recent_alerts:
        weight = alert_weights.get(alert.alert_type, 10)
        severity_multiplier = {
            "critical": 1.0,
            "high": 0.75,
            "medium": 0.5,
            "low": 0.25,
        }[alert.severity]

        score += weight * severity_multiplier

    # Score from win rate
    if wallet.win_count + wallet.loss_count >= 5:
        win_rate = wallet.win_count / (wallet.win_count + wallet.loss_count)
        if win_rate >= 0.90:
            score += 30
        elif win_rate >= 0.75:
            score += 15

    # Score from market concentration
    market_stats = get_wallet_market_stats(wallet.address)
    if market_stats:
        top_market = max(market_stats, key=lambda x: x.total_volume_usd)
        concentration = top_market.total_volume_usd / wallet.total_volume_usd
        if concentration >= 0.95:
            score += 15
        elif concentration >= 0.80:
            score += 10

    return min(score, 100.0)
```

---

## API Specification

### REST Endpoints

```yaml
# Wallets
GET /api/wallets
  Query params:
    - min_insider_score: float (0-100)
    - is_watched: bool
    - min_volume_usd: float
    - max_account_age_days: int
    - limit: int (default 50)
    - offset: int (default 0)
  Response: List[WalletSummary]

GET /api/wallets/{address}
  Response: WalletDetail (includes trades, alerts, market stats)

POST /api/wallets/{address}/watch
  Body: { reason: string, notify_threshold_usd: float }
  Response: Watchlist entry

DELETE /api/wallets/{address}/watch
  Response: 204 No Content


# Trades
GET /api/trades
  Query params:
    - wallet_address: string
    - market_id: string
    - min_volume_usd: float
    - since: datetime
    - limit: int
  Response: List[Trade]

GET /api/trades/live
  WebSocket endpoint for real-time trade feed
  Message format: Trade with flags


# Alerts
GET /api/alerts
  Query params:
    - status: 'new' | 'viewed' | 'actioned' | 'dismissed'
    - severity: 'low' | 'medium' | 'high' | 'critical'
    - alert_type: string
    - since: datetime
    - limit: int
  Response: List[Alert]

PUT /api/alerts/{id}
  Body: { status: string, action_taken: string }
  Response: Alert

GET /api/alerts/live
  WebSocket endpoint for real-time alerts
  Message format: Alert


# Markets
GET /api/markets
  Query params:
    - active: bool
    - category: string
    - search: string
    - limit: int
  Response: List[MarketSummary]

GET /api/markets/{condition_id}
  Response: MarketDetail (includes recent trades, suspicious activity)

GET /api/markets/{condition_id}/suspicious
  Response: List of flagged wallets/trades for this market


# Analytics
GET /api/analytics/summary
  Response: {
    total_alerts_24h: int,
    critical_alerts_24h: int,
    flagged_wallets: int,
    copy_trade_pnl: float,
  }

GET /api/analytics/leaderboard
  Query params:
    - metric: 'insider_score' | 'win_rate' | 'volume'
    - period: '24h' | '7d' | '30d'
  Response: List[WalletRanking]
```

### WebSocket Events

```typescript
// Trade feed
interface TradeEvent {
  type: "trade";
  data: {
    trade: Trade;
    wallet: WalletSummary;
    flags: string[];
    insider_score: number;
  };
}

// Alert feed
interface AlertEvent {
  type: "alert";
  data: Alert;
}

// Market update
interface MarketEvent {
  type: "market_update";
  data: {
    market_id: string;
    odds: number;
    volume_24h: number;
    suspicious_activity: boolean;
  };
}
```

---

## Dashboard Pages

### 1. Live Feed (`/`)

Real-time feed of all trades with insider scoring.

```
┌─────────────────────────────────────────────────────────────────────┐
│  🔴 LIVE FEED                                          [Filters ▼]  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │ 🚨 HIGH SCORE (78)                              2 seconds ago │ │
│  │                                                               │ │
│  │ 0x3f4...8a2 bought $15,420 YES on                            │ │
│  │ "Will Trump meet Xi before Feb 2026?"                        │ │
│  │                                                               │ │
│  │ Account age: 3 days | Total trades: 2 | Win rate: N/A        │ │
│  │ Flags: [new_wallet] [large_bet] [single_market]              │ │
│  │                                                               │ │
│  │ [View Wallet] [Add to Watchlist] [Copy Trade]                │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │ Score: 23                                       15 seconds ago │ │
│  │                                                               │ │
│  │ 0x8b1...f3c sold $2,100 NO on                                │ │
│  │ "Will Bitcoin reach $150k in January?"                       │ │
│  │                                                               │ │
│  │ Account age: 89 days | Total trades: 47 | Win rate: 52%      │ │
│  │                                                               │ │
│  │ [View Wallet]                                                │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  ... more trades ...                                                │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 2. Alerts (`/alerts`)

Filtered view of insider alerts.

```
┌─────────────────────────────────────────────────────────────────────┐
│  🚨 ALERTS                                                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Filter: [All ▼] [Critical] [High] [New Only]     Sort: [Newest ▼] │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │ 🔴 CRITICAL | new_wallet_large_bet            5 min ago | NEW │ │
│  │                                                               │ │
│  │ New wallet (1d) placed $42,000 bet                           │ │
│  │ Market: "Will Fed cut rates in January?"                     │ │
│  │ Confidence: 92%                                              │ │
│  │                                                               │ │
│  │ [View Details] [Copy Trade] [Dismiss] [Watch Wallet]         │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │ 🟠 HIGH | abnormal_win_rate                  23 min ago | NEW │ │
│  │                                                               │ │
│  │ Wallet has 88% win rate (15/17)                              │ │
│  │ Category: Crypto                                             │ │
│  │ Total PnL: +$34,200                                          │ │
│  │ Confidence: 78%                                              │ │
│  │                                                               │ │
│  │ [View Details] [Watch Wallet] [Dismiss]                      │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 3. Wallet Profile (`/wallets/{address}`)

Detailed view of a specific wallet.

```
┌─────────────────────────────────────────────────────────────────────┐
│  👤 WALLET: 0x3f4a...8a2c                         [Watch] [Block]  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  INSIDER SCORE                                              │   │
│  │  ████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  78/100 │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌────────────┐ │
│  │ Account Age  │ │ Total Volume │ │  Win Rate    │ │  Total PnL │ │
│  │   3 days     │ │   $47,200    │ │  100% (2/2)  │ │  +$12,400  │ │
│  └──────────────┘ └──────────────┘ └──────────────┘ └────────────┘ │
│                                                                     │
│  FLAGS: [new_wallet] [high_concentration] [large_positions]        │
│                                                                     │
│  ───────────────────────────────────────────────────────────────── │
│  MARKET BREAKDOWN                                                   │
│  ───────────────────────────────────────────────────────────────── │
│                                                                     │
│  Market                              Volume    Side   PnL   Status │
│  ─────────────────────────────────────────────────────────────────│
│  Will Trump meet Xi before Feb?     $42,000    YES   +$0    Open  │
│  Will Fed cut rates in January?      $5,200    NO  +$12k   Won ✓  │
│                                                                     │
│  ───────────────────────────────────────────────────────────────── │
│  TRADE HISTORY                                                      │
│  ───────────────────────────────────────────────────────────────── │
│                                                                     │
│  Time          Market                    Side  Size   Price  Flags │
│  ─────────────────────────────────────────────────────────────────│
│  2 min ago     Trump/Xi meeting          BUY   $42k   0.34   🚨    │
│  3 days ago    Fed rate cut              BUY   $5.2k  0.62         │
│                                                                     │
│  ───────────────────────────────────────────────────────────────── │
│  ALERTS FOR THIS WALLET (3)                                        │
│  ───────────────────────────────────────────────────────────────── │
│                                                                     │
│  • new_wallet_large_bet (CRITICAL) - 2 min ago                     │
│  • single_market_concentration (HIGH) - 2 min ago                  │
│  • high_slippage_tolerance (MEDIUM) - 2 min ago                    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 4. Market Analysis (`/markets/{id}`)

Suspicious activity for a specific market.

```
┌─────────────────────────────────────────────────────────────────────┐
│  📊 MARKET: Will Trump meet Xi before Feb 2026?                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Current Odds: YES 34% / NO 66%    Volume: $1.2M    Ends: Feb 1    │
│                                                                     │
│  ───────────────────────────────────────────────────────────────── │
│  🚨 SUSPICIOUS ACTIVITY DETECTED                                    │
│  ───────────────────────────────────────────────────────────────── │
│                                                                     │
│  • 3 new wallets (<7 days) betting YES in last 2 hours             │
│  • Combined volume: $67,000                                        │
│  • Odds moved: 28% → 34% (+6%)                                     │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │ Flagged Wallets                                               │ │
│  │                                                               │ │
│  │ Address        Age   Volume   Score  Action                   │ │
│  │ ────────────────────────────────────────────────────────────│ │
│  │ 0x3f4...8a2   3d    $42,000   78    [View] [Copy]            │ │
│  │ 0x9c2...1b4   1d    $18,000   85    [View] [Copy]            │ │
│  │ 0x7a8...3f9   5d    $7,000    62    [View] [Copy]            │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  ───────────────────────────────────────────────────────────────── │
│  RECENT LARGE TRADES                                                │
│  ───────────────────────────────────────────────────────────────── │
│                                                                     │
│  Time       Wallet         Side   Size     Price  Impact  Score   │
│  ────────────────────────────────────────────────────────────────│
│  2 min     0x3f4...8a2     YES   $42,000   0.34   +2.1%    78    │
│  15 min    0x9c2...1b4     YES   $18,000   0.32   +1.4%    85    │
│  1 hr      0x7a8...3f9     YES   $7,000    0.31   +0.8%    62    │
│  2 hr      0xf82...9a1     NO    $25,000   0.69   -1.2%    12    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 5. Watchlist (`/watchlist`)

Manually tracked wallets.

### 6. Copy Trades (`/copy-trades`)

Track performance of trades copied from alerts.

### 7. Analytics (`/analytics`)

Overall system performance, alert accuracy, copy trade PnL.

---

## Data Pipeline

### 1. Event Ingestion

```python
# Option A: Polygon WebSocket (real-time)
async def subscribe_to_trades():
    """Subscribe to OrderFilled events via WebSocket."""

    ws = await connect_polygon_ws()

    # Subscribe to CTF Exchange events
    await ws.subscribe({
        "address": CTF_EXCHANGE_ADDRESS,
        "topics": [ORDER_FILLED_TOPIC],
    })

    # Subscribe to NegRisk Exchange events
    await ws.subscribe({
        "address": NEGRISK_EXCHANGE_ADDRESS,
        "topics": [ORDER_FILLED_TOPIC],
    })

    async for event in ws:
        trade = parse_order_filled(event)
        await event_queue.put(trade)


# Option B: Subgraph Polling (simpler, slight delay)
async def poll_subgraph():
    """Poll Goldsky subgraph for new trades."""

    last_block = get_last_processed_block()

    while True:
        query = """
        {
            trades(
                where: { blockNumber_gt: %d }
                orderBy: blockNumber
                first: 1000
            ) {
                id
                maker
                taker
                tokenId
                makerAmount
                takerAmount
                price
                blockNumber
                timestamp
            }
        }
        """ % last_block

        result = await goldsky_client.query(query)

        for trade in result["trades"]:
            await event_queue.put(trade)
            last_block = max(last_block, trade["blockNumber"])

        await asyncio.sleep(5)  # Poll every 5 seconds
```

### 2. Trade Processing

```python
async def process_trade(raw_trade: dict):
    """Process a single trade through the detection pipeline."""

    async with db_session() as session:
        # 1. Parse and validate
        trade = Trade.from_raw(raw_trade)

        # 2. Get or create wallet
        wallet = await get_or_create_wallet(session, trade.wallet_address)

        # 3. Get market metadata
        market = await get_market(session, trade.market_id)
        if not market:
            market = await fetch_and_cache_market(trade.market_id)

        # 4. Enrich trade with context
        trade.market = market
        trade.mid_price_at_trade = await get_mid_price(trade.token_id)
        trade.slippage_percent = calculate_slippage(trade)

        # 5. Save trade
        session.add(trade)

        # 6. Update wallet stats
        await update_wallet_stats(session, wallet, trade)

        # 7. Run detection algorithms
        alerts = []

        alert = detect_new_wallet_large_bet(trade, wallet)
        if alert:
            alerts.append(alert)

        alert = detect_high_slippage_tolerance(trade, wallet)
        if alert:
            alerts.append(alert)

        alert = detect_market_impact(trade)
        if alert:
            alerts.append(alert)

        # 8. Save alerts
        for alert in alerts:
            alert.wallet_address = wallet.address
            alert.trade_id = trade.id
            alert.market_id = market.condition_id
            session.add(alert)

        # 9. Update insider score
        wallet.insider_score = calculate_insider_score(wallet, alerts)

        # 10. Broadcast to WebSocket clients
        await broadcast_trade(trade, wallet, alerts)

        await session.commit()
```

### 3. Periodic Tasks

```python
# Run every hour
async def periodic_coordination_detection():
    """Scan for coordinated wallet activity."""

    active_markets = await get_active_markets()

    for market in active_markets:
        alert = detect_coordinated_wallets(market.condition_id)
        if alert:
            await save_and_broadcast_alert(alert)


# Run after each market resolution
async def on_market_resolved(market_id: str, outcome: str):
    """Update win/loss stats and check for abnormal win rates."""

    # Get all positions in this market
    positions = await get_market_positions(market_id)

    for position in positions:
        won = (position.side == outcome)

        # Update wallet stats
        wallet = await get_wallet(position.wallet_address)
        if won:
            wallet.win_count += 1
        else:
            wallet.loss_count += 1

        # Check for abnormal win rate
        alert = detect_abnormal_win_rate(wallet)
        if alert:
            await save_and_broadcast_alert(alert)

        # Update category stats
        await update_category_stats(wallet, market.category, won, position.pnl)


# Run every 6 hours
async def periodic_score_recalculation():
    """Recalculate insider scores for all watched wallets."""

    watched = await get_watched_wallets()

    for wallet in watched:
        recent_alerts = await get_wallet_alerts(wallet.address, days=30)
        wallet.insider_score = calculate_insider_score(wallet, recent_alerts)
        await save_wallet(wallet)
```

---

## Tech Stack

| Component | Technology | Rationale |
|-----------|------------|-----------|
| **Language** | Python 3.11+ | Async support, Web3 libraries |
| **Web Framework** | FastAPI | Async, WebSocket support, auto docs |
| **Database** | PostgreSQL | JSONB, window functions, reliability |
| **Cache/Queue** | Redis | Pub/sub for WebSocket, event queue |
| **ORM** | SQLAlchemy 2.0 | Async support, type hints |
| **Web3** | web3.py | Polygon interaction |
| **GraphQL Client** | gql | Subgraph queries |
| **Frontend** | HTMX + Tailwind | Fast development, real-time updates |
| **Deployment** | Docker + Railway/Fly.io | Simple, scalable |

---

## Implementation Phases

### Phase 1: Foundation (Week 1-2)

**Goal**: Basic data pipeline and storage

- [ ] Project setup (repo, Docker, CI)
- [ ] Database schema and migrations
- [ ] Polygon RPC connection
- [ ] Subgraph client
- [ ] Trade ingestion pipeline
- [ ] Wallet profile creation
- [ ] Market metadata caching
- [ ] Basic REST API

**Deliverable**: System ingests and stores all Polymarket trades

### Phase 2: Detection (Week 3-4)

**Goal**: Core detection algorithms

- [ ] New Wallet Large Bet detector
- [ ] Single Market Concentration detector
- [ ] High Slippage Tolerance detector
- [ ] Market Impact detector
- [ ] Composite insider score calculation
- [ ] Alert storage and API
- [ ] Watchlist functionality

**Deliverable**: System generates alerts for suspicious activity

### Phase 3: Real-time (Week 5-6)

**Goal**: Live monitoring capabilities

- [ ] WebSocket server for trades
- [ ] WebSocket server for alerts
- [ ] Live feed dashboard page
- [ ] Alerts dashboard page
- [ ] Wallet profile page
- [ ] Basic filtering and search

**Deliverable**: Real-time dashboard showing suspicious trades

### Phase 4: Analysis (Week 7-8)

**Goal**: Market-level analysis and coordination detection

- [ ] Market analysis page
- [ ] Coordinated wallet detection
- [ ] Win rate tracking (post-resolution)
- [ ] Abnormal win rate detection
- [ ] Category-based statistics
- [ ] Historical analysis views

**Deliverable**: Full detection suite with market-level insights

### Phase 5: Polish (Week 9-10)

**Goal**: Production readiness

- [ ] Telegram bot for alerts
- [ ] Copy trade tracking
- [ ] Analytics dashboard
- [ ] Performance optimization
- [ ] Rate limiting and error handling
- [ ] Documentation
- [ ] Deployment and monitoring

**Deliverable**: Production-ready MVP

---

## Success Metrics

### Detection Quality
- **Alert precision**: >70% of critical alerts on trades that later prove profitable
- **Coverage**: Detect >80% of trades that move markets >10%
- **Latency**: <30 seconds from on-chain trade to alert

### System Performance
- **Uptime**: >99%
- **Trade processing**: <5 second latency
- **WebSocket latency**: <1 second

### User Value
- **Copy trade ROI**: Positive average PnL on copied trades
- **Alert actionability**: >50% of high/critical alerts viewed
- **Watchlist utility**: Watched wallets perform better than random

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Polygon RPC rate limits | Data gaps | Multiple RPC providers, subgraph fallback |
| False positives | Alert fatigue | Tunable thresholds, ML refinement post-MVP |
| Insiders adapt patterns | Reduced detection | Continuous algorithm updates |
| Polymarket API changes | Breaking changes | Abstract API layer, monitoring |
| High infrastructure costs | Budget overrun | Start with subgraph (free tier), scale later |

---

## Cost Estimate

### Infrastructure (Monthly)

| Service | Cost | Notes |
|---------|------|-------|
| PostgreSQL (managed) | $15-50 | Railway/Supabase |
| Redis (managed) | $10-30 | Upstash/Railway |
| Compute (API + workers) | $20-50 | Fly.io/Railway |
| Polygon RPC | $0-50 | Alchemy free tier, then paid |
| Subgraph queries | $0 | Goldsky free |
| **Total** | **$45-180/mo** | |

### Development (One-time)

| Phase | Effort | Notes |
|-------|--------|-------|
| Phase 1-2 | 80-100 hrs | Core pipeline |
| Phase 3-4 | 60-80 hrs | Real-time + analysis |
| Phase 5 | 40-60 hrs | Polish |
| **Total** | **180-240 hrs** | |

---

## Open Questions

1. **Copy trading execution**: Manual only for MVP, or semi-automated?
2. **Alert channels**: Web + Telegram, or add Discord/email?
3. **Historical backfill**: How far back to index? (cost vs value)
4. **Multi-user**: Single user MVP or multi-tenant from start?
5. **Monetization**: Personal tool or SaaS potential?

---

## Next Steps

1. Validate subgraph data availability (test queries)
2. Set up development environment
3. Create GitHub repo with CI/CD
4. Implement Phase 1 trade ingestion
5. Deploy minimal version to verify pipeline

---

## Appendix: Example Queries

### Goldsky Subgraph - Recent Trades

```graphql
{
  trades(
    first: 100
    orderBy: timestamp
    orderDirection: desc
  ) {
    id
    maker
    taker
    tokenId
    makerAmount
    takerAmount
    price
    timestamp
    blockNumber
    transactionHash
  }
}
```

### Goldsky Subgraph - Wallet Positions

```graphql
{
  positions(
    where: { user: "0x..." }
  ) {
    id
    user
    condition
    outcomeIndex
    balance
    averagePrice
    realizedPnl
  }
}
```

### Polygon RPC - OrderFilled Event

```python
# Event signature
ORDER_FILLED_TOPIC = Web3.keccak(text="OrderFilled(bytes32,address,address,uint256,uint256,uint256,uint256,uint256)")

# Decode event
def decode_order_filled(log):
    return {
        "order_hash": log.topics[1].hex(),
        "maker": decode_address(log.topics[2]),
        "taker": decode_address(log.topics[3]),
        "maker_asset_id": decode_uint256(log.data[0:32]),
        "taker_asset_id": decode_uint256(log.data[32:64]),
        "maker_amount_filled": decode_uint256(log.data[64:96]),
        "taker_amount_filled": decode_uint256(log.data[96:128]),
        "fee": decode_uint256(log.data[128:160]),
    }
```
