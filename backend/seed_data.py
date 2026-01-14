#!/usr/bin/env python3
"""
Seed script to populate the database with realistic fake trading data.
Run with: python seed_data.py
"""

import asyncio
import random
import uuid
import json
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Import models
from app.models.market import Market
from app.models.signal import Signal
from app.models.position import Position
from app.models.strategy import (
    CustomStrategy,
    AdvancedStrategy,
    AdvancedStrategySource,
    AdvancedStrategyPartialExit,
)
from app.database import Base

DATABASE_URL = "sqlite+aiosqlite:///./app.db"

# Realistic market questions for Polymarket
MARKET_QUESTIONS = [
    ("Will Bitcoin exceed $100,000 by end of Q1 2026?", "Crypto", 150000, 2500000),
    ("Will the Fed cut interest rates in January 2026?", "Economics", 85000, 1800000),
    ("Will SpaceX successfully land Starship on Mars by 2026?", "Science", 45000, 890000),
    ("Will AI pass the Turing test definitively by 2026?", "Technology", 62000, 1200000),
    ("Will Democrats win the 2026 midterm elections?", "Politics", 320000, 5600000),
    ("Will Tesla stock exceed $500 by March 2026?", "Stocks", 78000, 1450000),
    ("Will there be a major earthquake (7.0+) in California in 2026?", "Science", 25000, 450000),
    ("Will Netflix subscriber count exceed 300M by Q2 2026?", "Entertainment", 34000, 680000),
    ("Will Ethereum 2.0 fully transition by February 2026?", "Crypto", 92000, 1950000),
    ("Will Apple release AR glasses in 2026?", "Technology", 55000, 1100000),
    ("Will US inflation drop below 2% by mid-2026?", "Economics", 125000, 2800000),
    ("Will China's GDP growth exceed 5% in 2026?", "Economics", 48000, 920000),
    ("Will OpenAI release GPT-5 by Q1 2026?", "Technology", 180000, 3200000),
    ("Will gold prices exceed $2,500/oz by March 2026?", "Commodities", 67000, 1380000),
    ("Will Manchester United win the Premier League 2025-26?", "Sports", 42000, 780000),
    ("Will a nuclear fusion plant generate net energy by 2026?", "Science", 28000, 520000),
    ("Will TikTok be banned in the US by end of 2026?", "Politics", 95000, 2100000),
    ("Will the S&P 500 close above 6,000 in January 2026?", "Stocks", 210000, 4500000),
    ("Will Ukraine join NATO by end of 2026?", "Politics", 38000, 720000),
    ("Will autonomous vehicles be legal in 10+ US states by 2026?", "Technology", 51000, 980000),
    ("Will a COVID variant cause new lockdowns in 2026?", "Health", 72000, 1560000),
    ("Will Dogecoin exceed $1 by 2026?", "Crypto", 145000, 2900000),
    ("Will Amazon stock split again in 2026?", "Stocks", 29000, 580000),
    ("Will climate legislation pass US Congress in 2026?", "Politics", 85000, 1750000),
    ("Will Nvidia remain the top AI chip maker through 2026?", "Technology", 110000, 2300000),
    ("Will the Super Bowl 2026 have over 120M US viewers?", "Sports", 56000, 1150000),
    ("Will Apple's market cap exceed $4 trillion in 2026?", "Stocks", 165000, 3400000),
    ("Will a major airline declare bankruptcy in 2026?", "Business", 22000, 410000),
    ("Will quantum computing achieve quantum advantage in 2026?", "Technology", 31000, 620000),
    ("Will the EU approve a digital euro by end of 2026?", "Economics", 44000, 870000),
]

# Signal sources matching frontend
SIGNAL_SOURCES = [
    "Polymarket Alpha",
    "News Alerts",
    "Trading Bot Webhook",
    "Crypto Signals Pro",
    "Market Insider",
    "Alpha Seekers",
]

STRATEGY_NAMES = [
    ("Conservative Growth", "Low risk strategy with steady returns"),
    ("Aggressive Alpha", "High risk, high reward momentum trading"),
    ("News Momentum", "Trading based on breaking news signals"),
    ("Crypto Volatility", "Exploiting crypto market swings"),
    ("Value Hunter", "Finding undervalued prediction markets"),
]


def generate_uuid():
    return str(uuid.uuid4())


def random_date(start_days_ago: int, end_days_ago: int = 0) -> str:
    """Generate random ISO date string within range."""
    days_ago = random.randint(end_days_ago, start_days_ago)
    dt = datetime.now() - timedelta(days=days_ago)
    return dt.isoformat()


def future_date(days_ahead: int) -> str:
    """Generate future ISO date string."""
    dt = datetime.now() + timedelta(days=days_ahead)
    return dt.isoformat()


async def seed_database():
    """Main seeding function."""
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        # Create tables if they don't exist
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        print("Clearing existing data...")
        # Clear existing data
        await session.execute(Position.__table__.delete())
        await session.execute(Signal.__table__.delete())
        await session.execute(Market.__table__.delete())
        await session.execute(AdvancedStrategyPartialExit.__table__.delete())
        await session.execute(AdvancedStrategySource.__table__.delete())
        await session.execute(AdvancedStrategy.__table__.delete())
        await session.execute(CustomStrategy.__table__.delete())
        await session.commit()

        print("Seeding markets...")
        markets = []
        for i, (question, category, liquidity, volume) in enumerate(MARKET_QUESTIONS):
            market = Market(
                condition_id=f"0x{generate_uuid().replace('-', '')[:40]}",
                question=question,
                description=f"Market prediction for: {question}",
                market_slug=question.lower().replace(" ", "-").replace("?", "")[:50],
                end_date_iso=future_date(random.randint(14, 180)),
                clob_token_ids=json.dumps([generate_uuid(), generate_uuid()]),
                liquidity=liquidity + random.randint(-10000, 10000),
                volume=volume + random.randint(-50000, 50000),
                category=category,
                active=1,
                closed=0,
                created_at=random_date(90, 30),
                updated_at=datetime.now().isoformat(),
            )
            markets.append(market)
            session.add(market)

        await session.commit()
        print(f"  Created {len(markets)} markets")

        print("Seeding custom strategies...")
        custom_strategies = []
        custom_strategy_configs = [
            ("Safe Harbor", 15, 5, 3),
            ("Balanced Trader", 20, 10, 5),
            ("Momentum Play", 30, 15, 8),
        ]
        for name, tp, sl, trail in custom_strategy_configs:
            strategy = CustomStrategy(
                name=name,
                take_profit=tp,
                stop_loss=sl,
                trailing_stop=trail,
                partial_exit_percent=50 if random.random() > 0.5 else None,
                partial_exit_threshold=10 if random.random() > 0.5 else None,
                created_at=random_date(60, 30),
            )
            custom_strategies.append(strategy)
            session.add(strategy)

        await session.commit()
        print(f"  Created {len(custom_strategies)} custom strategies")

        print("Seeding advanced strategies...")
        advanced_strategies = []
        for name, desc in STRATEGY_NAMES:
            strategy = AdvancedStrategy(
                name=name,
                description=desc,
                default_take_profit=random.choice([15, 20, 25, 30]),
                default_stop_loss=random.choice([5, 10, 15]),
                default_trailing_stop=random.choice([3, 5, 8, None]),
                dynamic_trailing_enabled=random.choice([0, 1]),
                dynamic_trailing_base=20,
                dynamic_trailing_tight=5,
                dynamic_trailing_threshold=50,
                time_trailing_enabled=random.choice([0, 1]),
                time_trailing_start_hours=24,
                time_trailing_max_hours=72,
                time_trailing_tight=5,
                partial_exit_percent=random.choice([25, 50, None]),
                partial_exit_threshold=random.choice([10, 15, None]),
                min_source_win_rate=random.choice([0.5, 0.6, None]),
                min_source_profit_factor=random.choice([1.2, 1.5, None]),
                min_source_trades=random.choice([5, 10, None]),
                lookback_days=30,
                enabled=random.choice([0, 1, 1, 1]),  # 75% enabled
                created_at=random_date(45, 15),
                updated_at=datetime.now().isoformat(),
            )
            advanced_strategies.append(strategy)
            session.add(strategy)

        await session.commit()
        print(f"  Created {len(advanced_strategies)} advanced strategies")

        print("Seeding strategy sources...")
        for strategy in advanced_strategies:
            num_sources = random.randint(1, 3)
            used_sources = random.sample(SIGNAL_SOURCES, num_sources)
            for source_name in used_sources:
                source = AdvancedStrategySource(
                    strategy_id=strategy.id,
                    source=source_name,
                    take_profit=random.choice([None, strategy.default_take_profit + 5]),
                    stop_loss=random.choice([None, strategy.default_stop_loss - 2]),
                    trailing_stop=random.choice([None, 5, 8]),
                    position_size_multiplier=random.choice([0.5, 1.0, 1.5, 2.0]),
                )
                session.add(source)

        await session.commit()
        print("  Created strategy sources")

        print("Seeding partial exits...")
        for strategy in advanced_strategies:
            if random.random() > 0.4:  # 60% have partial exits
                exits = [
                    (1, 25, 10),
                    (2, 25, 20),
                    (3, 50, 30),
                ]
                for order, percent, threshold in exits[:random.randint(1, 3)]:
                    exit_rule = AdvancedStrategyPartialExit(
                        strategy_id=strategy.id,
                        exit_order=order,
                        exit_percent=percent,
                        threshold=threshold,
                    )
                    session.add(exit_rule)

        await session.commit()
        print("  Created partial exit rules")

        print("Seeding signals...")
        signals = []
        for i in range(150):  # Create 150 signals
            market = random.choice(markets)
            source = random.choice(SIGNAL_SOURCES)
            side = random.choice(["YES", "NO"])
            confidence = round(random.uniform(0.55, 0.95), 2)
            price = round(random.uniform(0.15, 0.85), 2)

            signal = Signal(
                signal_id=generate_uuid(),
                source=source,
                message_text=f"Signal detected: {side} on {market.question[:50]}... Confidence: {confidence*100:.0f}%",
                keywords=market.category,
                market_id=market.condition_id,
                token_id=generate_uuid(),
                market_question=market.question,
                side=side,
                confidence=confidence,
                price_at_signal=price,
                created_at=random_date(60, 0),
            )
            signals.append(signal)
            session.add(signal)

        await session.commit()
        print(f"  Created {len(signals)} signals")

        print("Seeding positions...")
        all_strategies = [(s, "custom") for s in custom_strategies] + [
            (s, "advanced") for s in advanced_strategies
        ]

        # Create mix of open and closed positions
        position_count = 0

        # Closed positions (historical)
        for _ in range(80):
            signal = random.choice(signals)
            strategy, strategy_type = random.choice(all_strategies)
            entry_price = round(random.uniform(0.20, 0.80), 4)

            # Simulate realistic P&L distribution (60% winners, 40% losers)
            is_winner = random.random() < 0.6
            if is_winner:
                pnl_percent = round(random.uniform(5, 35), 2)
            else:
                pnl_percent = round(random.uniform(-25, -5), 2)

            size = round(random.uniform(50, 500), 2)
            realized_pnl = round(size * (pnl_percent / 100), 2)
            exit_price = round(entry_price * (1 + pnl_percent / 100), 4)

            opened_at = random_date(60, 7)
            opened_dt = datetime.fromisoformat(opened_at)
            closed_dt = opened_dt + timedelta(days=random.randint(1, 14))

            position = Position(
                signal_id=signal.signal_id,
                strategy_id=strategy.id,
                strategy_name=strategy.name,
                market_id=signal.market_id,
                token_id=signal.token_id,
                market_question=signal.market_question,
                side=signal.side,
                entry_price=entry_price,
                current_price=exit_price,
                exit_price=exit_price,
                size=size,
                status="closed",
                unrealized_pnl=0,
                unrealized_pnl_percent=0,
                realized_pnl=realized_pnl,
                realized_pnl_percent=pnl_percent,
                source=signal.source,
                opened_at=opened_at,
                closed_at=closed_dt.isoformat(),
            )
            session.add(position)
            position_count += 1

        # Open positions (current)
        for _ in range(25):
            signal = random.choice(signals[-50:])  # Use recent signals
            strategy, strategy_type = random.choice(all_strategies)
            entry_price = round(random.uniform(0.25, 0.75), 4)

            # Current price with unrealized P&L
            price_change = round(random.uniform(-0.15, 0.20), 4)
            current_price = round(max(0.01, min(0.99, entry_price + price_change)), 4)

            size = round(random.uniform(100, 800), 2)
            unrealized_pnl_percent = round(((current_price - entry_price) / entry_price) * 100, 2)
            unrealized_pnl = round(size * (unrealized_pnl_percent / 100), 2)

            position = Position(
                signal_id=signal.signal_id,
                strategy_id=strategy.id,
                strategy_name=strategy.name,
                market_id=signal.market_id,
                token_id=signal.token_id,
                market_question=signal.market_question,
                side=signal.side,
                entry_price=entry_price,
                current_price=current_price,
                exit_price=None,
                size=size,
                status="open",
                unrealized_pnl=unrealized_pnl,
                unrealized_pnl_percent=unrealized_pnl_percent,
                realized_pnl=None,
                realized_pnl_percent=None,
                source=signal.source,
                opened_at=random_date(7, 0),
                closed_at=None,
            )
            session.add(position)
            position_count += 1

        await session.commit()
        print(f"  Created {position_count} positions (25 open, 80 closed)")

        print("\n" + "=" * 50)
        print("Database seeding complete!")
        print("=" * 50)
        print(f"  Markets: {len(markets)}")
        print(f"  Custom Strategies: {len(custom_strategies)}")
        print(f"  Advanced Strategies: {len(advanced_strategies)}")
        print(f"  Signals: {len(signals)}")
        print(f"  Positions: {position_count}")
        print("=" * 50)


if __name__ == "__main__":
    asyncio.run(seed_database())
